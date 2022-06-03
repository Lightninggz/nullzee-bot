import time
from re import search

import discord

from api_key import PREFIX
from helpers.events import Subscriber
from helpers.utils import get_user, list_one, role_ids
from helpers.constants import Role, Channel

ACHIEVEMENT_BORDERS = {
    0.2: "bronze",
    0.5: "silver",
    0.8: "gold"
}

achievements = {
    "Hello, World!": {
        "listeners": {
            "message": lambda msg: not msg.author.bot
        },
        "description": "Send your first message in the server",
        "value": 10,
        "db_rewards": {
            "experience": 25,
        },
    },
    "Level Collector I": {
        "listeners": {
            "level_up": lambda _, level: level >= 10
        },
        "description": "Reach level 10",
        "value": 5,
        "db_rewards": {
            "experience": 100
        },
    },
    "Level Collector II": {
        "listeners": {
            "level_up": lambda _, level: level >= 30
        },
        "description": "Reach level 30",
        "value": 10,
        "db_rewards": {
            "experience": 250,
        },
    },
    "Level Collector III": {
        "listeners": {
            "level_up": lambda _, level: level >= 50
        },
        "description": "Reach level 50",
        "value": 15,
        "db_rewards": {
            "experience": 500,
        },
    },
    "Role collector I": {
        "listeners": {
            "update_roles": lambda _, roles: len(roles) > 10
        },
        "description": "Have 10 roles",
        "value": 5,
    },
    "Role collector II": {
        "listeners": {
            "update_roles": lambda _, roles: len(roles) > 25
        },
        "description": "Have 25 roles",
        "value": 10
    },
    "Role collector III": {
        "listeners": {
            "update_roles": lambda _, roles: len(roles) > 50
        },
        "description": "Have 50 roles",
        "value": 15,
    },
    "Rich": {
        "listeners": {
            "update_roles": lambda ctx, roles: Role.BOOSTER in role_ids(roles)
            # "update_roles": lambda ctx, roles: print(Role)
        },
        "description": "Nitro boost the server",
        "value": 5,
    },
    "Prime Log": {
        "listeners": {
            "update_roles": lambda _, roles: Role.TWITCH_SUB in role_ids(roles)
        },
        "description": "Subscribe to Nullzee on twitch and link your account through discord!",
        "value": 5,
    },
    "Full of ideas": {
        "listeners": {
            "command": lambda _, name: name == "suggest"
        },
        "description": "Make your first suggestion",
        "value": 6,
        "db_rewards": {
            "experience": 500
        },
    },
    "Talkative I": {
        "listeners": {
            "update_roles": lambda _, roles: Role.VC_LORD in role_ids(roles)
        },
        "description": "Become a VC lord",
        "value": 5,
    },
    "Talkative II": {
        "listeners": {
            "update_roles": lambda _, roles: Role.VC_GOD in role_ids(roles)
        },
        "description": "Become a VC god",
        "value": 10,
    },
    "Mean": {
        "listeners": {
            "points_spent": lambda _, name: name == "staffNickChange"
        },
        "description": f"Purchase StaffNickChange from {PREFIX}shop",
        "value": 5,
    },
    "Frugal I": {
        "listeners": {
            "point_earned": lambda _, points: points >= 100
        },
        "description": "Save up 100 points",
        "value": 10,
    },
    "Frugal II": {
        "listeners": {
            "point_earned": lambda _, points: points >= 200
        },
        "description": "Save up 200 points",
        "value": 15,
    },
    "Frugal III": {
        "listeners": {
            "point_earned": lambda _, points: points >= 300
        },
        "description": "Save up 300 points",
        "value": 20,
    },
    "Necromancer": {
        "listeners": {
            "points_spent": lambda _, name: name == "deadChatPing"
        },
        "description": f"Purchase DeadChatPing from {PREFIX}shop",
        "value": 5,
    },
    "Up to date": {
        "listeners": {
            "update_roles": lambda _, roles: {Role.POLL_PING, Role.QOTD_PING, Role.EVENT_PING,
                                              Role.DEAD_CHAT_PING, Role.GIVEAWAY_PING,
                                              Role.ANNOUNCEMENT_PING, Role.SKYBLOCK_PING} <= set(
                role_ids(roles))
        },
        "description": "Have all ping roles",
        "value": 4,
    },
    "Agreeable": {
        "listeners": {
            "suggestion_stage_2": lambda _: True
        },
        "description": "Get 15 more upvotes than downvotes on one of your suggestions",
        "value": 5,
        "db_rewards": {
            "experience": 300,
        },
    },
    "Generous I": {
        "listeners": {
            "update_roles": lambda _, roles: Role.MINI_GIVEAWAY_DONOR in role_ids(roles)
        },
        "description": "Donate for a mini giveaway",
        "value": 5,
        "db_rewards": {
            "experience": 250,
            "points": 1
        },
    },
    "Generous II": {
        "listeners": {
            "update_roles": lambda _, roles: Role.GODLY_GIVEAWAY_DONOR in role_ids(roles)
        },
        "description": "Donate for a large giveaway",
        "value": 10,
        "db_rewards": {
            "experience": 750,
            "points": 3
        }

    },
    "Lucky!": {
        "listeners": {
            "update_roles": lambda _, roles: Role.LARGE_GIVEAWAY_WIN in role_ids(roles)
        },
        "description": "Win a large giveaway",
        "value": 5,
    },
    "Funny": {
        "listeners": {
            "pinned_starred": lambda _: True
        },
        "description": "Have one of your messages pinned or starred",
        "value": 5,

    },
    "Establishing Connections": {
        "listeners": {},
        "description": "Send a message in twitch chat after linking your twitch to your discord",
        "value": 5
    },
    "Bad boy": {
        "listeners": {
            "points_changed": lambda _, points: points > 0
        },
        "description": "Have some points refunded",
        "value": 3,
        "db_rewards": {
            "points": -1
        },
    },
    "Colourful": {
        "listeners": {
            "points_spent": lambda _, name: name == "EmbedColour"
        },
        "description": "Change your embed colour",
        "value": 3
    },
    "Even more colourful": {
        "listeners": {
            "points_spent": lambda _, name: name == "Rainbow"
        },
        "description": "Change the rainbow role colour",
        "value": 5
    },
    "Great Job": {
        "listeners": {
            "message": lambda msg: msg.guild and isinstance(msg.author, discord.Member) and
                                   msg.author.guild_permissions.manage_messages,
            "update_roles": lambda ctx, _: ctx.author.guild_permissions.manage_messages
        },
        "description": "Get any staff position",
        "value": -1,
        "db_rewards": {
            "experience": -69
        },
        "hidden": True
    },
    "Help at the wrong place": {
        "listeners": {
            "message": lambda ctx: ctx.guild and ctx.guild.get_member(
                540953289219375146) in ctx.message.mentions and "help" in ctx.message.content
        },
        "hidden": True,
        "value": 3
    },
    "New person": {
        "listeners": {
            "message": lambda msg: msg.guild and msg.author.joined_at.timestamp() + 604800 < time.time()
        },
        "description": "Be on the server for more than a week",
        "value": 2
    },
    "Getting older": {
        "listeners": {
            "message": lambda msg: msg.guild and msg.author.joined_at.timestamp() + 2628000 < time.time()
        },
        "description": "Be on the server for more than a month",
        "value": 5
    },
    "Old man": {
        "listeners": {
            "message": lambda msg: msg.guild and msg.author.joined_at.timestamp() + 15768000 < time.time()
        },
        "description": "Be on the server for over half a year",
        "value": 10
    },
    "QOTD Responder": {
        "listeners": {
            "message": lambda msg: msg.channel.id == Channel.QOTD_ANSWERS
        },
        "description": "Answer a QOTD for the first time",
        "value": 3
    },
    "OG member": {
        "listeners": {
            "update_roles": lambda _, roles: list_one(role_ids(roles), *Role.legacy())
        },
        "description": "Have a legacy role",
        "value": 5
    },
    "Event winner": {
        "listeners": {
            "update_roles": lambda _, roles: Role.EVENT_WINNER in role_ids(roles)
        },
        "description": "Win an event",
        "value": 10
    },
    "Nullzee knowledge": {
        "listeners": {
            "points_spent": lambda _, name: name == "AskNullzee",
        },
        "description": "Buy AskNullzee once",
        "value": 5
    },
    "Waste": {
        "listeners": {
            "waste": lambda _, points: points >= 50
        },
        "description": "Waste 50+ points",
        "value": 5
    },
    "Huge waste": {
        "listeners": {
            "waste": lambda _, points: points >= 100
        },
        "description": "Waste 100+ points",
        "value": 10
    },
    "Largest waste": {
        "listeners": {
            "waste": lambda _, points: points >= 250
        },
        "description": "Waste 250+ points",
        "value": 15
    },
    "Hypixel Linked": {
        "listeners": {
            "hypixel_link": lambda _: True
        },
        "description": "Link hypixel and discord accounts",
        "value": 5
    },
    "Advertising Champ": {
        "listeners": {
            "message": lambda msg: msg.channel.id == Channel.SELF_PROMO
        },
        "description": "Send an advertisement in #self-promo",
        "value": 2,
        "hidden": True,
    },
    "VC Afker": {
        "listeners": {
            "vc_minute_gain": lambda _, minutes: minutes > 43800
        },
        "description": "Have a month total time in VCs",
        "value": 15
    },
    # TODO: these on twitch bot
    "Stream viewer": {
        "listeners": {},
        "description": "Have 24h watchtime in Nullzee's stream",
        "value": 5
    },
    "Stream fan": {
        "listeners": {},
        "description": "Have 3 Days watchtime in Nullzee's stream",
        "value": 10
    },
    "Kindness": {
        "listeners": {
            "message": lambda ctx: ctx.guild and ctx.guild.me in ctx.message.mentions and (
                    "hi" in ctx.message.content.lower() or "hello" in ctx.message.content.lower())
        },
        "description": "Say Hi to the bot",
        "value": 2
    },
    "Talented": {
        "listeners": {
            "update_roles": lambda _, roles: Role.TALENTED in role_ids(roles)
        },
        "description": "Produce something pretty cool",
        "value": 5
    },
    "QOTD suggestion": {
        "listeners": {
            "points_spent": lambda _, name: name == "QOTD"
        },
        "description": "Suggest a QOTD from the shop",
        "value": 5
    },
    "Generic": {
        "listeners": {
            "message": lambda ctx: search("dirt to (.{4,})", ctx.message.content.lower())
        },
        "description": "Send a \"Dirt to...\" message",
        "value": 3,
        "hidden": True
    },
    "Nullzee Simp": {
        "listeners": {
            "update_roles": lambda _, roles: Role.SkyblockRole.MEGA_FAN in role_ids(roles)
        },
        "description": "Have the mega fan role",
        "value": 3,

    },
    "Gooby": {
        "listeners": {
            "command": lambda _, name: name == "gooby"
        },
        "description": f"Use the {PREFIX}gooby command",
        "value": 4,
        "hidden": True
    },
    "Crikey": {
        "listeners": {
            "command": lambda _, name: name == "crikey"
        },
        "description": f"Use the {PREFIX}crikey command",
        "value": 4,
        "hidden": True
    },
    "Wholesome": {
        "listeners": {
            "command": lambda _, name: name == "hug"
        },
        "description": f"Use the {PREFIX}hug command",
        "value": 4,
        "hidden": True
    },
    "Twitch Main": {
        "listeners": {},
        "description": "",
        "value": 0,
        "hidden": True
    },
    "Never gonna give you up": {
        "listeners": {
            "message": lambda ctx: list_one(ctx.message.content, "https://youtube.com/watch?v=dQw4w9WgXcQ")
        },
        "description": "",
        "value": 4,
        "hidden": True
    },
    "Fairy soul imposter": {
        "listeners": {
            "message": lambda ctx: ctx.message.content.lower().startswith("-claimroles timedeo")
        },
        "description": "",
        "value": 4,
        "hidden": True
    },
    "Nullzee advertisement": {
        "listeners": {
            "message": lambda ctx: ctx.channel.id == Channel.SELF_PROMO and "discord.gg/nullzee" in ctx.message.content.lower()
        },
        "description": "",
        "value": 4,
        "hidden": True
    },
    "Cute": {
        "listeners": {
            "message": lambda ctx: ctx.channel.id == Channel.PETS and ctx.message.attachments
        },
        "description": "",
        "value": 5,
        "hidden": True
    },
    "Vanity": {
        "listeners": {
            "command": lambda _, name: name == "avatar"
        },
        "description": "",
        "value": 3,
        "hidden": True
    },
    "Gamer": {
        "listeners": {
            "level_up": lambda ctx, _: ctx.channel.id == Channel.BOT_GAMES
        },
        "description": "",
        "value": 5,
        "hidden": True
    },
    "Muted": {
        "listeners": {
            "message": lambda ctx: ctx.channel.id == Channel.NO_MIC and ctx.author.voice and ctx.author.voice.self_mute
        },
        "description": "",
        "value": 5,
        "hidden": True
    },
    "Childish": {
        "listeners": {
            "message": lambda ctx: ctx.command and ctx.command.name == "maths" and "8008135" in ctx.message.content
        },
        "description": "Write `8008135` on a particular calculator",
        "value": 2,
        "hidden": False
    },

}


async def award_achievement(ctx, data, name):
    if ctx.author.bot:
        return
    if name in data["achievements"]:
        return
    string = ""
    # if "cb" in achievements[name]:
    #     await achievements[name]["cb"](ctx)
    if "response" in achievements[name]:
        await ctx.send(achievements[name]["response"].format(ctx))
    if "db_rewards" in achievements[name]:
        await ctx.bot.user_coll.update_one({"_id": str(ctx.author.id)}, {"$inc": achievements[name]["db_rewards"]})
        string += f" and earned {','.join(f'{v} {k}' for k, v in achievements[name]['db_rewards'].items())}"
    channel = ctx.author if "hidden" in achievements[name] and achievements[name]["hidden"] else ctx
    try:
        await channel.send(f"Congratulations {ctx.author.mention}, you just achieved `{name}`{string}!")
    except discord.Forbidden:
        return
    await ctx.bot.user_coll.update_one({"_id": str(ctx.author.id)},
                               {"$set": {f"achievements.{name}": time.time()},
                               "$inc": {"achievement_points": achievements[name]["value"]}})


def listeners_for(event):
    return [z for z in achievements if "listeners" in achievements[z] and event in achievements[z]["listeners"]]


award_queue = {}

subscriber = Subscriber()


@subscriber.listen_all()
async def listen(event, ctx, *args, **kwargs):
    for achievement in listeners_for(event):
        user_data = kwargs.pop("user_data", None)
        if achievements[achievement]["listeners"][event](ctx, *args, **kwargs):
            if ctx.author.id in award_queue:
                if achievement in award_queue[ctx.author.id]:
                    continue
                else:
                    award_queue[ctx.author.id].append(achievement)
            else:
                award_queue[ctx.author.id] = [achievement]
            user_data = user_data or await get_user(ctx.bot, ctx.author)
            await award_achievement(ctx, user_data, achievement)
            award_queue[ctx.author.id].remove(achievement)
