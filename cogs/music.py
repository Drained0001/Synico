import datetime
import discord
import wavelink
from discord.ext import commands
from cogs.errors import dj_perms
from main import Bot
from utils import QueueList, TrackConverter, start_menu


class Player(wavelink.Player):
    def __init__(self, channel: discord.TextChannel, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bot = channel.guild.me
        self._channel = channel
        self.queue = wavelink.Queue()

    async def next(self, skip: bool = False):
        try:
            track = self.queue.get()
            await self.play(track, replace=skip)
        except wavelink.QueueEmpty:
            await self.stop()
            await self._channel.send("No songs remaining in queue.", delete_after=15)

    async def stop(self):
        await self.disconnect(force=True)
        return await super().stop()

    async def tracks(self):
        yt_url = "https://www.youtube.com/results?search_query="
        cutoff = 10
        page = 1
        embeds = []
        queue = [track for track in self.queue]
        for slice in range(0, self.queue.count, cutoff):
            embed: discord.Embed = discord.Embed(
                title=f"{len(queue)} songs in queue",
                description="\n".join(
                    [
                        f"{index}. \
                        [{track.query if isinstance(track, wavelink.PartialTrack) else track.info['title']}]({f'{yt_url}{track.query}'.replace(' ', '+') if isinstance(track, wavelink.PartialTrack) else track.info['uri']})\
                        {'' if isinstance(track, wavelink.PartialTrack) else f'- {datetime.timedelta(seconds=track.duration)}'}"
                        for index, track in enumerate(
                            queue[slice : slice + cutoff], start=slice + 1
                        )
                    ]
                ),
                color=0x2ECC71,
            )
            embed.set_footer(text=f"Page {page}/{(len(queue) // cutoff) + 1}")
            embeds.append(embed)
            page += 1

        return embeds


class Music(commands.Cog):
    """
    A module for playing music.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.cooldown = commands.CooldownMapping.from_cooldown(
            1.0, 3.0, commands.BucketType.user
        )

    async def cog_check(self, ctx: commands.Context):
        bucket = self.cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandError(
                f"Woah! Slow down, please. Try again in {round(retry_after)} second(s)!"
            )

        return True

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node {node.identifier} is ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player: Player, track: wavelink.Track):

        embed = discord.Embed(
            title=f"Now playing {track.title}", url=track.uri, color=0x2ECC71
        )
        embed.set_thumbnail(
            url=f"https://i.ytimg.com/vi_webp/{track.identifier}/maxresdefault.webp"
        )
        embed.set_footer(
            text=f"Track length: {datetime.timedelta(seconds=track.duration)} | {player.queue.count} tracks in queue."
        )
        await player._channel.send(embed=embed, delete_after=15)

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, player: Player, track: wavelink.Track, reason: str
    ):
        if reason != "REPLACED":
            await player.next()

    @commands.Cog.listener()
    async def on_wavelink_track_exception(
        self, player: Player, track: wavelink.Track, error
    ):
        await player.next(True)

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(
        self, player: Player, track: wavelink.Track, threshold
    ):
        await player.next(True)

    @commands.command()
    async def play(
        self,
        context: commands.Context,
        *,
        query: TrackConverter = commands.Option(
            description="A song or playlist from Youtube, Spotify, or Soundcloud."
        ),
    ):
        """
        Play a song or playlist from Youtube, Spotify, or Soundcloud.
        """
        player: Player = context.bot.node.get_player(context.guild)
        if isinstance(query, list):
            for track in query:
                try:
                    player.queue.put(track)
                except TypeError:
                    pass

            if len(query) > 1:
                await context.send(
                    f"Added {query[0].title} + {len(query)} track(s) to the queue. {query[0].title}'s position {player.queue.find_position(query[0]) + 1}/{player.queue.count}.",
                    ephemeral=True,
                )

            elif len(query) == 1:
                await context.send(
                    f"Added {query[0].title} to the queue. Position {player.queue.find_position(query[0]) + 1}/{player.queue.count}.",
                    ephemeral=True,
                )

        elif query:
            player.queue.put(query)
            if player.queue.count >= 1:
                await context.send(
                    f"Added {query.title} to the queue. Position {player.queue.find_position(query) + 1}/{player.queue.count}.",
                    ephemeral=True,
                )

        else:
            await context.send(f"No results found.", ephemeral=True)

    @commands.command(name="queue")
    async def queue(self, context: commands.Context):
        """
        Display the current song queue.
        """
        player: Player = context.bot.node.get_player(context.guild)
        if player and len(player.queue) >= 1:
            tracks = await player.tracks()
            await context.send("Retrieving tracks...", ephemeral=True)
            return await start_menu(context, QueueList(tracks), hidden=False)

        else:
            await context.send("No tracks in queue.", ephemeral=True)

    @commands.command()
    async def skip(self, context: commands.Context):
        """
        Skips the current song.
        """
        player: Player = context.bot.node.get_player(context.guild)
        await context.send("Skipping...", delete_after=5)
        await player.next(True)

    @commands.command()
    async def pause(self, context: commands.Context):
        """
        Pauses current song.
        """
        player: Player = context.bot.node.get_player(context.guild)
        if player.is_paused():
            await context.send("Already paused.", ephemeral=True)

        elif player.is_playing():
            await player.pause()
            await context.send("Paused song.", delete_after=5)

    @commands.command()
    async def resume(self, context: commands.Context):
        """
        Resumes current song.
        """
        player: Player = context.bot.node.get_player(context.guild)
        if player.is_paused():
            await player.resume()
            await context.send("Resumed song.", delete_after=5)

        elif player.is_playing():
            await context.send("Already playing.", ephemeral=True)

    @commands.command()
    async def stop(self, context: commands.Context):
        """
        Clears the queue and stops playing music.
        """
        player: Player = context.bot.node.get_player(context.guild)
        if player:
            await context.send("Exiting...", delete_after=5)
            await player.stop()
            return

        await context.send("Not currently playing any tracks.", ephemeral=True)

    @play.before_invoke
    async def ensure_voice(self, context: commands.Context):
        if context.voice_client is None:
            if context.author.voice:
                player = Player(context.channel)
                vc: Player = await context.author.voice.channel.connect(cls=player)
                return player

            raise commands.CommandError("Author not connected to a voice channel.")

        elif not context.bot.node.get_player(context.guild):
            await context.voice_client.disconnect(force=True)
            player = Player(context.channel)
            vc: Player = await context.author.voice.channel.connect(cls=player)
            return vc

        elif context.voice_client:
            if not context.author.voice:
                raise commands.CommandError(
                    f"Author not connected to {context.voice_client.channel.mention}."
                )

    @pause.before_invoke
    @resume.before_invoke
    @skip.before_invoke
    @stop.before_invoke
    async def invoke_check(self, context: commands.Context):
        player: Player = context.bot.node.get_player(context.guild)

        can_run = dj_perms(context)
        if context.voice_client and player:
            if not can_run:
                raise commands.CommandError(f"Command only usable to mods/admins.")

            elif not context.author.voice:
                raise commands.CommandError(
                    f"Author not connected to {context.voice_client.channel.mention}."
                )

        elif not context.voice_client or not player:
            raise commands.CommandError("Not playing any tracks currently.")

    @play.after_invoke
    async def add_track(self, context: commands.Context):
        player: Player = context.bot.node.get_player(context.guild)
        if not player.is_playing():
            try:
                track = player.queue.get()
                await player.play(track, replace=False)
            except wavelink.QueueEmpty:
                pass


def setup(bot: Bot):
    bot.add_cog(Music(bot))
