from EZPaginator import Paginator
from discord.ext import commands, tasks
import discord
from discord.ext.commands import BucketType

from achievements.achievements import achievements
from achievements.images import achievement_page, achievement_timeline, achievement_timeline_animated, BackgroundMeta, \
    background_preview, BackgroundConverter, BoxBorderMeta, BoxBorderConverter, box_border_preview
from api_key import user_coll
from helpers.constants import Role
from helpers.events import Emitter, Subscriber
from helpers.utils import get_user, ShallowContext, get_file_json, Embed, save_file_json
from math import ceil
import typing
import os
import json
import time

import imageio


subscriber = Subscriber()


def generate_static_background_previews():
    data = BackgroundMeta.get()
    previews = []
    for bg in data:
        if BackgroundMeta.get()[bg].preview:
            previews.append(imageio.v2.imread(background_preview(bg)))
    imageio.mimsave(f"image_cache/static_background_previews/animated.gif", previews, fps=0.5)


def generate_static_boxborder_previews():
    data = BoxBorderMeta.get()
    previews = []
    for bg in data:
        if BoxBorderMeta.get()[bg].preview:
            previews.append(imageio.v2.imread(box_border_preview(bg)))
    imageio.mimsave(f"image_cache/static_boxborder_previews/animated.gif", previews, fps=0.5)


def generate_static_pages():
    images = []
    for i in range(ceil(len({k: v for k, v in achievements.items() if "hidden" not in v}) / 3)):
        images.append(imageio.v2.imread(achievement_page(i, f"image_cache/static_achievements/page_{i}.png")))
    imageio.mimsave(f"image_cache/static_achievements/animated.gif", images, fps=0.5)


async def get_inventory(user, inv, name):
    user_data = await get_user(user)
    bgs = user_data["achievement_inventory"][inv]
    return await Embed(user, title=f"Your {name} inventory", description="\n".join(bgs)).user_colour()


async def get_bg_inv(user):
    return await get_inventory(user, "backgrounds", "background")


async def get_bb_inv(user):
    return await get_inventory(user, "box_borders", "box-border")


# TODO: merge bb_shop and bg_shop with a generic achievement_shop function
class Achievements(commands.Cog, name="Achievements"):
    """The achievements system"""

    def __init__(self, bot):
        self.hidden = True
        self.bot: commands.Bot = bot
        self.emitter = Emitter()
        self.clear_image_cache.start()
        generate_static_pages()
        generate_static_background_previews()
        generate_static_boxborder_previews()

    def cog_unload(self):
        self.clear_image_cache.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @tasks.loop(minutes=1)
    async def clear_image_cache(self):
        for filename in os.listdir("image_cache/user_achievements"):
            if filename.endswith(".json"):
                with open(filename) as f:
                    cached_data = json.load(f)
                if cached_data["last_called"] + 600 < time.time():
                    for image_filename in cached_data["image_files"]:
                        os.remove(image_filename)
                    os.remove(filename)

    @clear_image_cache.before_loop
    async def before_clear_image_cache(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.type == discord.MessageType.pins_add:
            ctx = await self.bot.get_context((await message.channel.pins())[0])
            await self.emitter.emit("pinned_starred", ctx)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            await self.emitter.emit("update_roles", await ShallowContext.create(after), after.roles)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        await self.emitter.emit("command", ctx, ctx.command.name)

    @commands.command(name="listachievements", aliases=["lac"])
    @commands.cooldown(10, 1, BucketType.user)
    async def list_achievements(self, ctx, page: int = None):
        try:
            file_loc = "image_cache/static_achievements/" + (f"page_{page - 1}.png" if page else "animated.gif")
            await ctx.send(file=discord.File(file_loc))
        except FileNotFoundError:
            await ctx.send("There aren't that many pages!")

    @staticmethod
    @subscriber.listen("update_roles")
    async def on_roles_update(ctx, roles):
        role_ids = [z.id for z in roles]
        new_cosmetics = {"backgrounds": [], "box_borders": []}
        for cosmetic_type, cosmetic_name in zip([BackgroundMeta, BoxBorderMeta], list(new_cosmetics.keys())):
            for cos, cos_data in [(z, cosmetic_type.get()[z]) for z in cosmetic_type.get()]:
                if cos_data.role_req:
                    role_checks = []
                    for role in cos_data.role_req:
                        role_checks.append(Role[role.upper()] in role_ids)
                    if not ((cos_data.role_req_strategy == "all" and False in role_checks) or (True not in role_checks)):
                        new_cosmetics[cosmetic_name].append(cos)
        await user_coll.update_one(
            {"_id": str(ctx.author.id)},
            {"$addToSet": {f"achievement_inventory.{k}": {"$each": v} for k, v in new_cosmetics.items()}}
        )

    @commands.command(aliases=["ac"])
    @commands.cooldown(10, 1, BucketType.user)
    async def achievements(self, ctx, user: typing.Optional[discord.Member] = None, page: int = None):
        user = user if user else ctx.author
        user_data = await get_user(user)
        if not user_data["achievements"]:
            return await ctx.send("You haven't gained any achievements yet!")
        user_data["background_image"] = user_data["background_image"] if "background_image" in user_data else "default"
        if not page:
            await achievement_timeline_animated(user, user_data)
            await ctx.send(file=discord.File(f"image_cache/user_achievements/{user.id}_animated.gif"))
        else:
            try:
                did_create = await achievement_timeline(user, user_data, page)
            except ValueError:
                return await ctx.send("You don't have that many pages!")
            user_page_path = f"image_cache/user_achievements/{user.id}"
            await ctx.send(file=discord.File(f"{user_page_path}_{page}.png"))
            if not did_create:
                return
            cache_data = get_file_json(user_page_path)
            cache_data["regen_animated"] = True
            save_file_json(cache_data, user_page_path)

    @commands.command(name="achievementhelp", aliases=["achievementshelp", "achelp"])
    async def achievement_help(self, ctx):
        """Explains how the achievement system works"""
        embed = discord.Embed(title="Achievements", colour=0x00ff00)
        embed.add_field(
            name="How it works",
            value="You can complete achievements by doing various things within the server, such as sending messages "
                  "or gaining roles. Each achievement will reward you with a certain number of \"achievement points\", "
                  "these can be used to purchase background images and borders for the achievement commands",
            inline=False
        )
        embed.add_field(
            name="Commands",
            value="`-listachievements` : view a list of all non-hidden achievements\n"
                  "`-achievements` : view a timeline of your achievements",
            inline=False
        )
        embed.add_field(
            name="Borders",
            value="The border around your achievement timeline changes as you complete more achievements",
            inline=False
        )
        embed.add_field(
            name="Cosmetics",
            value="There are several cosmetic items that you can earn/purchase. There are exclusive backgrounds for "
                  "nitro boosters and twitch subs for example. You can buy cosmetics with \"achievement points\" "
                  "using the commands below",
            inline=False
        )
        embed.add_field(
            name="Cosmetic commands",
            value="`-backgrounds` : view all commands for changing your background image\n"
                  "`-boxborder` : view all commands for changing your box-border\n"
                  "`-inventory` : view both your background and box-border inventory at once",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["inv"])
    async def inventory(self, ctx):
        """View all of your achievement backgrounds and box borders"""
        bg_embed = (await get_bg_inv(ctx.author)).set_footer(text="page 1 of 2")
        bb_embed = (await get_bb_inv(ctx.author)).set_footer(text="page 2 of 2")
        msg = await ctx.send(embed=bg_embed)
        await Paginator(self.bot, msg, embeds=[bg_embed, bb_embed], timeout=60, use_extend=False, only=ctx.author).start()

    @commands.group(name="boxBorder", invoke_without_command=True, aliases=["bb"])
    async def box_border(self, ctx):
        """Boxborder related commands"""
        await ctx.send(embed=discord.Embed(
            title="-boxBorder",
            description="\n".join([f":arrow_right: `{ctx.PREFIX}boxBorder {z.name} {z.signature}`"
                                   for z in self.box_border.commands]),
            colour=0x00ff00
        ))

    @box_border.command(name="shop")
    async def bb_shop(self, ctx):
        """The boxborder shop"""
        user_data = await get_user(ctx.author)
        balance = user_data["achievement_points"]
        backgrounds = [f"{z} - {BoxBorderMeta.get()[z].cost} achievement points" for z in BoxBorderMeta.get()
                       if BoxBorderMeta.get()[z].purchasable]
        embed = await Embed(ctx.author, title=f"Achievement box-border shop - {balance}",
                            description="\n".join(backgrounds)).user_colour()
        await ctx.send(embed=embed)

    @box_border.command(name="preview")
    @commands.cooldown(10, 1, BucketType.user)
    async def bb_preview(self, ctx, *, image: BoxBorderConverter = None):
        """Preview the boxborders"""
        await ctx.send(file=discord.File(
            f"image_cache/static_boxborder_previews/{f'{image}.png' if image else 'animated.gif'}"
        ))

    @box_border.command(name="inventory", aliases=["inv"])
    async def bb_inventory(self, ctx):
        """View your boxborders"""
        embed = await get_bb_inv(ctx.author)
        await ctx.send(embed=embed)

    @box_border.command(name="select", aliases=["equip"])
    async def bb_select(self, ctx, *, item: BoxBorderConverter):
        """Select which boxborder you would like to use"""
        user_data = await get_user(ctx.author)
        if item not in user_data["achievement_inventory"]["box_borders"]:
            return await ctx.send("You have not unlocked that border yet!")
        await user_coll.update_one({"_id": str(ctx.author.id)}, {"$set": {"box_border": item}})
        await ctx.send(f"Successfully set your current box-border to `{item}`")

    @box_border.command(name="purchase", aliases=["buy"])
    async def bb_purchase(self, ctx, *, item: BoxBorderConverter):
        """Purchase a new boxborder"""
        user_data = await get_user(ctx.author)
        item_data = BoxBorderMeta.get()[item]
        if item in user_data["achievement_inventory"]["box_borders"]:
            return await ctx.send("You have already unlocked this box-border")
        if not item_data.purchasable:
            return await ctx.send("This border is not purchasable")
        if item_data.cost > user_data["achievement_points"]:
            return await ctx.send("You cannot afford this!")
        await user_coll.update_one({"_id": str(ctx.author.id)}, {"$push": {"achievement_inventory.box_borders": item},
                                                                "$inc": {"achievement_points": -item_data.cost}})
        await ctx.send(f"Successfully purchased `{item}` for {item_data.cost} achievement points")

    @commands.group(invoke_without_command=True, aliases=["backgrounds", "bg"])
    async def background(self, ctx):
        """Background related commands"""
        await ctx.send(embed=discord.Embed(
            title="-background",
            description="\n".join([f":arrow_right: `{ctx.PREFIX}background {z.name} {z.signature}`"
                                   for z in self.background.commands]),
            colour=0x00ff00
        ))

    @background.command(name="shop")
    async def bg_shop(self, ctx):
        """The background shop"""
        user_data = await get_user(ctx.author)
        balance = user_data["achievement_points"]
        backgrounds = [f"{z} - {BackgroundMeta.get()[z].cost} achievement points" for z in BackgroundMeta.get()
                       if BackgroundMeta.get()[z].purchasable]
        embed = await Embed(ctx.author, title=f"Achievement background shop - {balance}",
                            description="\n".join(backgrounds)).user_colour()
        await ctx.send(embed=embed)

    @background.command(name="preview")
    @commands.cooldown(10, 1, BucketType.user)
    async def bg_preview(self, ctx, *, image: BackgroundConverter = None):
        """Preview the backgrounds"""
        await ctx.send(file=discord.File(
            f"image_cache/static_background_previews/{f'{image}.png' if image else 'animated.gif'}"
        ))

    @background.command(name="inventory", aliases=["inv"])
    async def bg_inventory(self, ctx):
        """View your backgrounds"""
        embed = await get_bg_inv(ctx.author)
        await ctx.send(embed=embed)

    @background.command(name="select", aliases=["equip"])
    async def bg_select(self, ctx, *, item: BackgroundConverter):
        """Select which background you would like to use"""
        user_data = await get_user(ctx.author)
        if item not in user_data["achievement_inventory"]["backgrounds"]:
            return await ctx.send("You have not unlocked that background yet!")
        await user_coll.update_one({"_id": str(ctx.author.id)}, {"$set": {"background_image": item}})
        await ctx.send(f"Successfully set your current background image to `{item}`")

    @background.command(name="purchase", aliases=["buy"])
    async def bg_purchase(self, ctx, *, item: BackgroundConverter):
        """Purchase a new background"""
        user_data = await get_user(ctx.author)
        item_data = BackgroundMeta.get()[item]
        if item in user_data["achievement_inventory"]["backgrounds"]:
            return await ctx.send("You have already unlocked this background")
        if not item_data.purchasable:
            return await ctx.send("This image is not purchasable")
        if item_data.cost > user_data["achievement_points"]:
            return await ctx.send("You cannot afford this!")
        await user_coll.update_one({"_id": str(ctx.author.id)}, {"$push": {"achievement_inventory.backgrounds": item},
                                                                 "$inc": {"achievement_points": -item_data.cost}})
        await ctx.send(f"Successfully purchased `{item}` for {item_data.cost} achievement points")


async def setup(bot):
    await bot.add_cog(Achievements(bot))
