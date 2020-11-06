from helpers import utils
import time

def warn_payload(*, offender_id, mod_id, reason):
    return {
        "id": utils.nanoId(),
        "offender_id": offender_id,
        "mod_id": mod_id,
        "type": "warn",
        "reason": reason,
        "timestamp": round(time.time())
    }

def mute_payload(*, offender_id, mod_id, reason, duration):
    return {
        "id": utils.nanoId(),
        "offender_id": offender_id,
        "mod_id": mod_id,
        "type": "mute",
        "reason": reason,
        "timestamp": round(time.time()),
        "duration": duration,
        "ends": round(time.time()) + duration if duration else 0,
        "active": True,
        "permanent": True if not duration else False
    }

def ban_payload(*, offender_id, mod_id, reason, duration):
    return {
        "id": utils.nanoId(),
        "offender_id": offender_id,
        "mod_id": mod_id,
        "type": "ban",
        "reason": reason,
        "timestamp": round(time.time()),
        "duration": duration,
        "ends": round(time.time()) + duration if duration else 0,
        "active": True,
        "permanent": True if not duration else False
    }