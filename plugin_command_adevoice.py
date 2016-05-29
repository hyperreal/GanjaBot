#
#  This file is part of Magnet2.
#  Copyright (c) 2011  Grom PE
#
#  Magnet2 is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or     
#  (at your option) any later version.                                   
#
#  Magnet2 is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Magnet2.  If not, see <http://www.gnu.org/licenses/>.
#
import time, xmpp
from magnet_api import *
from magnet_utils import *

adevoice_db = {}

def check_adevoice(bot, room, nick, jid=None):
  if bot.in_roster(room, nick) and bot.roster[room][nick][ROSTER_ROLE] == 'moderator': return
  prefix = bot.get_config(room, 'db_prefix')
  if not prefix in adevoice_db: return
  if nick in adevoice_db[prefix]:
    reason = adevoice_db[prefix][nick]['reason']
    reason = reason and 'Nick banned (%s)'%(reason) or 'Nick banned.'
    bot.client.send(iq_set_role(room, nick, 'visitor', reason))
  else:
    if not jid and not bot.in_roster(room, nick): return
    if not jid: jid = bot.roster[room][nick][ROSTER_JID]
    if not jid: return
    jid = xmpp.JID(jid).getStripped().lower()
    if jid in adevoice_db[prefix]:
      reason = adevoice_db[prefix][jid]['reason']
      reason = reason and 'Banned (%s)'%(reason) or 'Banned.'
      bot.client.send(iq_set_role(room, nick, 'visitor', reason))

def command_adevoice(bot, room, nick, access_level, parameters, message):
  if parameters == '': return "Expected <target nick or JID> [reason]"
  (target, reason) = separate_target_reason(bot, room, parameters)

  if target in bot.roster[room] and bot.roster[room][target][ROSTER_ROLE] == 'moderator':
    return 'Can not autodevoice a moderator.'

  prefix = bot.get_config(room, 'db_prefix')
  if not prefix in adevoice_db: adevoice_db[prefix] = {}

  if target in adevoice_db[prefix]:
    return '%s is already in autodevoice.'%(target)

  adevoice_db[prefix][target] = {
    'time': time.time(),
    'reason': reason
  }
  check_adevoice(bot, room, target)
  return '%s is autodevoiceed.'%(target)
    
def command_deladevoice(bot, room, nick, access_level, parameters, message):
  if not parameters: return "Expected <target nick or JID>"
  target = parameters
  if target[-1] == ' ': target = target[0:-1]

  prefix = bot.get_config(room, 'db_prefix')
  if not prefix in adevoice_db or not target in adevoice_db[prefix]:
    return '%s is not autodevoiceed.'%(target)

  del adevoice_db[prefix][target]
  bot.client.send(iq_set_role(room, target, 'participant', 'reason'))
  return 'Autodevoice lifted from %s.'%(target)
    
def command_adevoiceed(bot, room, nick, access_level, parameters, message):
  prefix = bot.get_config(room, 'db_prefix')

  if not parameters:
    # list all
    if message.getType() == 'groupchat':
      # for privacy reasons
      return "Specify the target, or use without parameters in private."
    if not prefix in adevoice_db or len(adevoice_db[prefix]) == 0:
      return "Autodevoice list is empty."
    return "Autodevoiceed: %s."%(', '.join(adevoice_db[prefix].keys()))

  target = parameters
  if target[-1] == ' ': target = target[0:-1]

  if not prefix in adevoice_db or not target in adevoice_db[prefix]:
    return '%s is not autodevoiceed.'%(target)

  seconds = time.time()-adevoice_db[prefix][target]['time']
  ago = timeformat(seconds)
  reason = adevoice_db[prefix][target]['reason']
  return '%s is set to autodevoice %s ago with reason: %s.'%(target, ago, reason)
    
def event_nick_changed(bot, (presence, room, nick, newnick)):
  check_adevoice(bot, room, newnick)

def event_joined(bot, (presence, room, nick, jid, role, affiliation, status, status_text)):
  if role != 'moderator':
    check_adevoice(bot, room, nick, jid)

def event_room_roster(bot, (presence, room, nick, jid, role, affiliation, status, status_text)):
  if role != 'moderator':
    check_adevoice(bot, room, nick, jid)

def load(bot):
  global adevoice_db
  adevoice_db = bot.load_database('adevoice') or {}
  bot.add_command('adevoice', command_adevoice, LEVEL_ADMIN)
  bot.add_command('deladevoice', command_deladevoice, LEVEL_ADMIN)
  bot.add_command('adevoiceed', command_adevoiceed, LEVEL_ADMIN)

def save(bot):
  bot.save_database('adevoice', adevoice_db)

def unload(bot):
  pass

def info(bot):
  return 'Autodevoice plugin v1.0.1'
