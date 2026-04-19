from __future__ import annotations

import asyncio
import logging

import discord
import lavalink
from discord import app_commands
from discord.ui import Button, View
from lavalink.errors import ClientError

from musicbot.config import Settings

LOGGER = logging.getLogger(__name__)


def format_duration(duration_ms: int) -> str:
    total_seconds = max(duration_ms // 1000, 0)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


class LavalinkVoiceClient(discord.VoiceProtocol):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable) -> None:
        self.client = client
        self.channel = channel
        self.guild_id = channel.guild.id
        self._destroyed = False

        lavalink_client = getattr(client, "lavalink", None)
        if lavalink_client is None:
            raise RuntimeError("Lavalink client is not ready.")

        self.lavalink: lavalink.Client = lavalink_client

    async def on_voice_server_update(self, data: dict) -> None:
        LOGGER.info("VoiceProtocol forwarding VOICE_SERVER_UPDATE for guild %s", self.guild_id)
        await self.lavalink.voice_update_handler({"t": "VOICE_SERVER_UPDATE", "d": data})

    async def on_voice_state_update(self, data: dict) -> None:
        channel_id = data["channel_id"]
        LOGGER.info("VoiceProtocol forwarding VOICE_STATE_UPDATE for guild %s (channel=%s)", self.guild_id, channel_id)

        if not channel_id:
            await self._destroy()
            return

        self.channel = self.client.get_channel(int(channel_id))
        await self.lavalink.voice_update_handler({"t": "VOICE_STATE_UPDATE", "d": data})

    async def connect(
        self,
        *,
        timeout: float,
        reconnect: bool,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(
            channel=self.channel,
            self_mute=self_mute,
            self_deaf=self_deaf,
        )

    async def disconnect(self, *, force: bool = False) -> None:
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        if player is not None and (force or player.is_connected):
            await self.channel.guild.change_voice_state(channel=None)
            player.channel_id = None

        await self._destroy()

    async def _destroy(self) -> None:
        self.cleanup()

        if self._destroyed:
            return

        self._destroyed = True
        try:
            await self.lavalink.player_manager.destroy(self.guild_id)
        except ClientError:
            pass


class MusicBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True

        super().__init__(intents=intents)
        self.settings = settings
        self.tree = app_commands.CommandTree(self)
        self.lavalink: lavalink.Client | None = None
        self.node_ready = asyncio.Event()
        self.tree.add_command(play_command)
        self.tree.add_command(skip_command)
        self.tree.add_command(pause_command)
        self.tree.add_command(resume_command)
        self.tree.add_command(stop_command)
        self.tree.add_command(leave_command)
        self.tree.add_command(queue_command)
        self.tree.add_command(now_playing_command)

    async def setup_hook(self) -> None:
        if self.settings.discord_server_id:
            guild = discord.Object(id=self.settings.discord_server_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            LOGGER.info("Synced app commands to server %s", self.settings.discord_server_id)
        else:
            await self.tree.sync()
            LOGGER.info("Synced global app commands")

    async def on_ready(self) -> None:
        if self.user is None:
            return

        if self.lavalink is None:
            self.lavalink = lavalink.Client(self.user.id)
            self.lavalink.add_event_hooks(self)
            self.lavalink.add_node(
                host=self.settings.lavalink_host,
                port=self.settings.lavalink_port,
                password=self.settings.lavalink_password,
                region="eu",
                name="main",
                ssl=self.settings.lavalink_secured,
                connect=True,
            )
            LOGGER.info(
                "Connecting to Lavalink at %s:%s",
                self.settings.lavalink_host,
                self.settings.lavalink_port,
            )

    @lavalink.listener(lavalink.NodeReadyEvent)
    async def on_lavalink_node_ready(self, event: lavalink.NodeReadyEvent) -> None:
        self.node_ready.set()
        LOGGER.info("Lavalink node %s is ready (session %s)", event.node.name, event.session_id)

    @lavalink.listener(lavalink.TrackStartEvent)
    async def on_lavalink_track_start(self, event: lavalink.TrackStartEvent) -> None:
        LOGGER.info("Started track in guild %s: %s", event.player.guild_id, event.track.title)

    @lavalink.listener(lavalink.PlayerErrorEvent)
    async def on_lavalink_player_error(self, event: lavalink.PlayerErrorEvent) -> None:
        LOGGER.exception("Playback error in guild %s", event.player.guild_id, exc_info=event.original)

    @lavalink.listener(lavalink.QueueEndEvent)
    async def on_lavalink_queue_end(self, event: lavalink.QueueEndEvent) -> None:
        guild = self.get_guild(event.player.guild_id)
        if guild is None:
            return

        try:
            await guild.change_voice_state(channel=None)
        except discord.DiscordException:
            LOGGER.exception("Failed to disconnect from voice in guild %s", event.player.guild_id)

        try:
            await event.player.destroy()
        except Exception:
            LOGGER.exception("Failed to destroy Lavalink player for guild %s", event.player.guild_id)

    async def close(self) -> None:
        if self.lavalink is not None:
            await self.lavalink.close()
        await super().close()


def guild_only() -> app_commands.Check:
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            raise app_commands.CheckFailure("This command can only be used in a server.")
        return True

    return app_commands.check(predicate)


def require_lavalink(bot: MusicBot) -> lavalink.Client:
    if bot.lavalink is None:
        raise app_commands.AppCommandError("The Lavalink client is still starting up.")
    return bot.lavalink


async def wait_for_lavalink(bot: MusicBot) -> lavalink.Client:
    client = require_lavalink(bot)

    if not bot.node_ready.is_set():
        try:
            await asyncio.wait_for(bot.node_ready.wait(), timeout=15)
        except TimeoutError as exc:
            raise app_commands.AppCommandError("Lavalink is not ready yet. Try again in a few seconds.") from exc

    return client


def get_existing_player(bot: MusicBot, guild_id: int | None) -> lavalink.DefaultPlayer | None:
    if guild_id is None or bot.lavalink is None:
        return None
    return bot.lavalink.player_manager.get(guild_id)


def get_user_voice_channel(interaction: discord.Interaction) -> discord.VoiceChannel:
    if interaction.guild is None:
        raise app_commands.AppCommandError("This command must be used in a server.")

    user_voice = getattr(interaction.user, "voice", None)
    if not user_voice or not user_voice.channel:
        raise app_commands.AppCommandError("Join a voice channel first.")

    if not isinstance(user_voice.channel, discord.VoiceChannel):
        raise app_commands.AppCommandError("Join a standard voice channel to use the music bot.")

    return user_voice.channel


async def ensure_player(interaction: discord.Interaction) -> lavalink.DefaultPlayer:
    if interaction.guild is None or interaction.guild_id is None:
        raise app_commands.AppCommandError("This command must be used in a server.")

    bot = interaction.client
    if not isinstance(bot, MusicBot):
        raise app_commands.AppCommandError("Bot client is not available.")

    lavalink_client = await wait_for_lavalink(bot)
    channel = get_user_voice_channel(interaction)
    player = lavalink_client.player_manager.create(interaction.guild_id)
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        member = interaction.guild.me
        if member is None:
            raise app_commands.AppCommandError("The bot is not visible in this server yet.")

        permissions = channel.permissions_for(member)
        if not permissions.connect or not permissions.speak:
            raise app_commands.AppCommandError("The bot needs Connect and Speak permissions for that voice channel.")

        try:
            voice_client = await channel.connect(cls=LavalinkVoiceClient, self_deaf=True)
        except discord.DiscordException as exc:
            raise app_commands.AppCommandError(f"Discord could not connect the bot to that voice channel: {exc}") from exc
    elif voice_client.channel != channel:
        await interaction.guild.change_voice_state(channel=channel, self_deaf=True)

    if not isinstance(voice_client, LavalinkVoiceClient):
        raise app_commands.AppCommandError("The existing voice client is not Lavalink-managed. Disconnect it and try again.")

    return player


async def search_tracks(bot: MusicBot, query: str) -> lavalink.LoadResult:
    lavalink_client = await wait_for_lavalink(bot)

    if query.startswith(("http://", "https://")):
        result = await lavalink_client.get_tracks(query)
    else:
        result = await lavalink_client.get_tracks(f"ytsearch:{query}")

    if result.load_type == lavalink.LoadType.ERROR and result.error is not None:
        raise app_commands.AppCommandError(result.error.message)

    if not result.tracks:
        raise app_commands.AppCommandError("No playable tracks were found.")

    return result


def pick_tracks(load_result: lavalink.LoadResult) -> list[lavalink.AudioTrack]:
    if load_result.load_type == lavalink.LoadType.PLAYLIST:
        return list(load_result.tracks)

    if load_result.load_type == lavalink.LoadType.TRACK:
        return [load_result.tracks[0]]

    if load_result.selected_track is not None:
        return [load_result.selected_track]

    return [load_result.tracks[0]]


def describe_requester(guild: discord.Guild | None, requester_id: int) -> str:
    if guild is None:
        return str(requester_id)

    member = guild.get_member(requester_id)
    return member.display_name if member else str(requester_id)


def get_player_from_interaction(interaction: discord.Interaction) -> lavalink.DefaultPlayer | None:
    bot = interaction.client
    if not isinstance(bot, MusicBot):
        return None

    return get_existing_player(bot, interaction.guild_id)


def create_track_embed(
    *,
    title: str,
    track: lavalink.AudioTrack,
    requester: discord.Member | discord.User,
    status: str,
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=f"**{track.title}**",
        color=discord.Color.from_rgb(255, 184, 77),
        url=track.uri,
    )
    embed.add_field(name="Artist", value=track.author or "Unknown", inline=True)
    embed.add_field(name="Length", value=format_duration(track.duration), inline=True)
    embed.add_field(name="Status", value=status, inline=True)
    embed.set_footer(text=f"Requested by {requester.display_name}")

    artwork = getattr(track, "artwork_url", None)
    if artwork:
        embed.set_thumbnail(url=artwork)

    return embed


def create_queue_embed(player: lavalink.DefaultPlayer, guild: discord.Guild | None) -> discord.Embed:
    embed = discord.Embed(
        title="Flash105 Queue",
        color=discord.Color.from_rgb(255, 184, 77),
    )

    if player.current is not None:
        requester = describe_requester(guild, getattr(player.current, "requester", 0))
        embed.add_field(
            name="Now Playing",
            value=f"**{player.current.title}**\n{player.current.author} ({requester})",
            inline=False,
        )

    if player.queue:
        upcoming = []
        for index, track in enumerate(player.queue[:10], start=1):
            requester = describe_requester(guild, getattr(track, "requester", 0))
            upcoming.append(f"{index}. **{track.title}** - {track.author} ({requester})")
        embed.add_field(name="Up Next", value="\n".join(upcoming), inline=False)
    else:
        embed.add_field(name="Up Next", value="Nothing queued.", inline=False)

    return embed


class PlayerControls(View):
    def __init__(self) -> None:
        super().__init__(timeout=900)

    async def _get_player(self, interaction: discord.Interaction) -> lavalink.DefaultPlayer | None:
        player = get_player_from_interaction(interaction)
        if player is None:
            await interaction.response.send_message("The bot is not connected to voice.", ephemeral=True)
            return None
        return player

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary, custom_id="flash105:pause")
    async def pause(self, interaction: discord.Interaction, _: Button) -> None:
        player = await self._get_player(interaction)
        if player is None:
            return

        if not player.is_playing:
            await interaction.response.send_message("Nothing is currently playing.", ephemeral=True)
            return

        await player.set_pause(True)
        await interaction.response.send_message("Paused.", ephemeral=True)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.success, custom_id="flash105:resume")
    async def resume(self, interaction: discord.Interaction, _: Button) -> None:
        player = await self._get_player(interaction)
        if player is None:
            return

        if not player.paused:
            await interaction.response.send_message("Playback is not paused.", ephemeral=True)
            return

        await player.set_pause(False)
        await interaction.response.send_message("Resumed.", ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary, custom_id="flash105:skip")
    async def skip(self, interaction: discord.Interaction, _: Button) -> None:
        player = await self._get_player(interaction)
        if player is None:
            return

        if not player.is_playing:
            await interaction.response.send_message("Nothing is currently playing.", ephemeral=True)
            return

        await player.skip()
        await interaction.response.send_message("Skipped.", ephemeral=True)

    @discord.ui.button(label="Queue", style=discord.ButtonStyle.secondary, custom_id="flash105:queue")
    async def queue(self, interaction: discord.Interaction, _: Button) -> None:
        player = await self._get_player(interaction)
        if player is None:
            return

        if player.current is None and not player.queue:
            await interaction.response.send_message("The queue is empty.", ephemeral=True)
            return

        await interaction.response.send_message(embed=create_queue_embed(player, interaction.guild), ephemeral=True)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.danger, custom_id="flash105:leave")
    async def leave(self, interaction: discord.Interaction, _: Button) -> None:
        player = await self._get_player(interaction)
        if player is None:
            return

        player.queue.clear()
        await player.stop()
        if interaction.guild is not None and interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.send_message("Disconnected.", ephemeral=True)


@app_commands.command(name="play", description="Queue a song from YouTube via Lavalink.")
@app_commands.describe(query="A song title, YouTube URL, or playlist URL")
@guild_only()
async def play_command(interaction: discord.Interaction, query: str) -> None:
    await interaction.response.defer(thinking=True)
    bot = interaction.client
    if not isinstance(bot, MusicBot):
        raise app_commands.AppCommandError("Bot client is not available.")

    player = await ensure_player(interaction)
    load_result = await search_tracks(bot, query)
    tracks = pick_tracks(load_result)

    started_now = not player.is_playing and player.current is None and not player.paused
    for track in tracks:
        player.add(track, requester=interaction.user.id)

    if started_now:
        await player.play()

    if len(tracks) == 1:
        track = tracks[0]
        verb = "Now playing" if started_now else "Queued"
        embed = create_track_embed(
            title=f"Flash105 - {verb}",
            track=track,
            requester=interaction.user,
            status="Playing now" if started_now else "Added to queue",
        )
        await interaction.followup.send(embed=embed, view=PlayerControls())
        return

    playlist_name = load_result.playlist_info.name or "playlist"
    await interaction.followup.send(f"Queued `{len(tracks)}` tracks from **{playlist_name}**.")


@app_commands.command(name="skip", description="Skip the currently playing track.")
@guild_only()
async def skip_command(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)
    bot = interaction.client
    if not isinstance(bot, MusicBot):
        raise app_commands.AppCommandError("Bot client is not available.")

    player = get_existing_player(bot, interaction.guild_id)
    if player is None or not player.is_playing:
        await interaction.followup.send("Nothing is currently playing.", ephemeral=True)
        return

    await player.skip()
    await interaction.followup.send("Skipped.", ephemeral=True)


@app_commands.command(name="pause", description="Pause playback.")
@guild_only()
async def pause_command(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)
    bot = interaction.client
    if not isinstance(bot, MusicBot):
        raise app_commands.AppCommandError("Bot client is not available.")

    player = get_existing_player(bot, interaction.guild_id)
    if player is None or not player.is_playing:
        await interaction.followup.send("Nothing is currently playing.", ephemeral=True)
        return

    await player.set_pause(True)
    await interaction.followup.send("Paused.", ephemeral=True)


@app_commands.command(name="resume", description="Resume playback.")
@guild_only()
async def resume_command(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)
    bot = interaction.client
    if not isinstance(bot, MusicBot):
        raise app_commands.AppCommandError("Bot client is not available.")

    player = get_existing_player(bot, interaction.guild_id)
    if player is None or not player.paused:
        await interaction.followup.send("Playback is not paused.", ephemeral=True)
        return

    await player.set_pause(False)
    await interaction.followup.send("Resumed.", ephemeral=True)


@app_commands.command(name="stop", description="Stop playback and clear the queue.")
@guild_only()
async def stop_command(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)
    bot = interaction.client
    if not isinstance(bot, MusicBot):
        raise app_commands.AppCommandError("Bot client is not available.")

    player = get_existing_player(bot, interaction.guild_id)
    if player is None:
        await interaction.followup.send("The bot is not connected to voice.", ephemeral=True)
        return

    player.queue.clear()
    await player.stop()
    await interaction.followup.send("Stopped playback and cleared the queue.", ephemeral=True)


@app_commands.command(name="leave", description="Disconnect from voice and clear the queue.")
@guild_only()
async def leave_command(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)
    bot = interaction.client
    if not isinstance(bot, MusicBot):
        raise app_commands.AppCommandError("Bot client is not available.")

    player = get_existing_player(bot, interaction.guild_id)
    if player is None or interaction.guild is None:
        await interaction.followup.send("The bot is not connected to voice.", ephemeral=True)
        return

    player.queue.clear()
    await player.stop()
    if interaction.guild.voice_client is not None:
        await interaction.guild.voice_client.disconnect(force=True)
    await interaction.followup.send("Disconnected.", ephemeral=True)


@app_commands.command(name="queue", description="Show the current queue.")
@guild_only()
async def queue_command(interaction: discord.Interaction) -> None:
    bot = interaction.client
    if not isinstance(bot, MusicBot):
        raise app_commands.AppCommandError("Bot client is not available.")

    player = get_existing_player(bot, interaction.guild_id)
    if player is None or (player.current is None and not player.queue):
        await interaction.response.send_message("The queue is empty.", ephemeral=True)
        return

    lines: list[str] = []
    if player.current is not None:
        requester = describe_requester(interaction.guild, getattr(player.current, "requester", 0))
        lines.append(
            f"Now playing: **{player.current.title}** - {player.current.author} ({requester})"
        )

    for index, track in enumerate(player.queue[:10], start=1):
        requester = describe_requester(interaction.guild, getattr(track, "requester", 0))
        lines.append(f"{index}. {track.title} - {track.author} ({requester})")

    await interaction.response.send_message("\n".join(lines), ephemeral=True)


@app_commands.command(name="nowplaying", description="Show the currently playing track.")
@guild_only()
async def now_playing_command(interaction: discord.Interaction) -> None:
    bot = interaction.client
    if not isinstance(bot, MusicBot):
        raise app_commands.AppCommandError("Bot client is not available.")

    player = get_existing_player(bot, interaction.guild_id)
    if player is None or player.current is None:
        await interaction.response.send_message("Nothing is currently playing.", ephemeral=True)
        return

    track = player.current
    requester = describe_requester(interaction.guild, getattr(track, "requester", 0))
    embed = discord.Embed(
        title="Flash105 - Now Playing",
        description=f"**{track.title}**",
        color=discord.Color.from_rgb(255, 184, 77),
        url=track.uri,
    )
    embed.add_field(name="Artist", value=track.author or "Unknown", inline=True)
    embed.add_field(name="Length", value=format_duration(track.duration), inline=True)
    embed.add_field(name="Requested by", value=requester, inline=True)

    artwork = getattr(track, "artwork_url", None)
    if artwork:
        embed.set_thumbnail(url=artwork)

    await interaction.response.send_message(
        embed=embed,
        view=PlayerControls(),
        ephemeral=True,
    )


@play_command.error
@skip_command.error
@pause_command.error
@resume_command.error
@stop_command.error
@leave_command.error
@queue_command.error
@now_playing_command.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    LOGGER.exception("App command failed: %s", error)

    original = error.original if isinstance(error, app_commands.CommandInvokeError) else error
    message = str(original) if str(original) else "The command failed unexpectedly."

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)
