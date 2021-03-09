

class Constant(type):
    _constants = {}

    def __new__(mcs, *args, **kwargs):
        self = super(Constant, mcs).__new__(mcs, *args, **kwargs)
        mcs._constants[self] = args[2]
        return self

    def __getitem__(self, item):
        return self._constants[self][item]



class Role(metaclass=Constant):
    BOOSTER     = 668724083718094869
    TWITCH_SUB  = 668736363297898506
    VC_LORD     = 682656964123295792
    VC_GOD      = 804095281036525638
    EVENT_PING  = 733698696159690838
    ANNOUNCEMENT_PING = 738691495317602344
    GIVEAWAY_PING = 735238184832860402
    POLL_PING   = 738691450417709077
    DEAD_CHAT_PING = 749178299518943343
    QOTD_PING   = 749178235845345380
    TRAINEE     = 675031583954173986
    STAFF       = 667953757954244628
    ADMIN       = 685027474522112000
    EVENT_WINNER= 734023673236947076
    TALENTED    = 703135588819271701
    MEGA_FAN    = 678152766891360298
    TRUSTED_MEMBER = 668722188764839946
    CARP_GANG   = 743940100018405497
    BANANA_GANG = 743940139901780010
    SB_SWEAT    = 668735481458065438
    GOOBY       = 810126462509645845

    # categories:
    @classmethod
    def legacy(cls):
        return [
            cls.TRUSTED_MEMBER,
            cls.CARP_GANG,
            cls.BANANA_GANG,
            cls.SB_SWEAT,
            cls.GOOBY
        ]


class Channel(metaclass=Constant):
    GIVEAWAY        = 667960870697041942
    MINI_GIVEAWAY   = 735236900830576643
    QOTD_ANSWERS    = 749631176431370260
    SELF_PROMO      = 667960498448367668