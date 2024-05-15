import re
import os
import sched
import time
from datetime import datetime, timezone, timedelta

from telethon.errors.rpcerrorlist import(
    MessageAuthorRequiredError,
    ChatIdInvalidError,
    MessageIdInvalidError,
)
from telethon import (
    TelegramClient,
    events,
)
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import (
    PeerChannel,
    PeerUser,
    PeerChat,
)

api_id = os.environ.get("SSAFUM_apiID" , "17067170")
api_hash = os.environ.get("SSAFUM_apiHASH", "3c4474c248c7e0e566e702150f20321b")

client = TelegramClient('main', api_id, api_hash)

channel_forwards = "ssafum"

channels = []
    
main_channel = {
    'id': 2010895052,
    'title': 'انجمن های علمی فردوسی مشهد',
}
main_group = {
    'id': 2082842980,
    'title': 'SSA FUM Admins',
}
keywords = []  # keywords: if the post include added keywords, won't be sent to the admins group

filename='channel_ids.txt'

def read_channel_ids():
    """Read Telegram channel IDs from a file and store them in an array."""
    channel_ids = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                channel_ids.append(line.strip())
    except FileNotFoundError:
        pass  # File doesn't exist yet, so return an empty array
    return channel_ids

def save_channel_id(channel_id, new = False):
    """Save Telegram channel ID to a file."""
    if new:
        with open(filename, 'w'):
            pass
        
    with open(filename, 'a+') as file:
        file.write(str(channel_id) + '\n')

def remove_channel_id(channel_id):
    """Remove Telegram channel ID from a file."""
    with open(filename, 'r') as file:
        lines = file.readlines()
    with open(filename, 'w') as file:
        for line in lines:
            if line.strip() != str(channel_id):
                file.write(line)
                

@client.on(events.NewMessage)
async def my_event_handler(event):
    if re.match(r'(?i).*(hello)$', event.raw_text, re.IGNORECASE):
        user = PeerUser((await event.message.get_sender()).id)
        user = await client.get_entity(user)
        await event.reply('Hi {}👋🏻, I\'m Admin of Student Science Association Ferdowsi University of mashhad, '
                          '@soroush_fathi programmed me to do this job🤠'.format(user.first_name))


@client.on(events.NewMessage)
async def commands(event):
    global channel_forwards
    
    strs = event.raw_text.split('\n')
    try:
        chat = await client.get_entity(PeerChat((await event.message.get_chat())).chat_id)
        # Admins can just use these commands(events from SSA FUM Admins)
        if chat.id == main_group['id']:
            # add channels: join the given channels and send there post for admins
            if re.findall(r'(?i)^/add_channel', event.raw_text):
                if len(strs) == 1:
                    await event.reply('لیست کانال ها برای افزودن خالی است🙂')
                else:
                    tmp = await event.reply('⏳در حال بررسی کانال ها ...')
                    res = ''
                    async with client.action(chat, 'typing'):
                        for i, item in zip(range(len(strs)), strs[1:]):
                            if item[0] == '@':
                                item = item[1:]
                            try:
                                channel = await client.get_entity(item)
                                if await client(JoinChannelRequest(channel)):
                                    res += '✅عضویت کانال {}({}ام): موفق'.format(channel.title, i + 1) + '\n'
                                    
                                save_channel_id(channel.id)
                            except ValueError:
                                res += '❌عضویت کانال {}ام: ناموفق(کانالی با این نشانی برای عضویت وجود ندارد)\n'.format(
                                    i+1)
                            except :
                                res += '❌عضویت کانال {}ام: ناموفق(برای ورودی فقط آدرس کانال را وارد کنید)\n'.format(i+1)
                await client.delete_messages(chat, tmp)
                await client.send_message(chat, res, reply_to=event.message)
            elif re.findall(r'(?i)^/remove_channel', event.raw_text):
                if len(strs) == 1:
                    await event.reply('لیست کانال ها برای ترک کردن خالی است🙂')
                else:
                    res = ''
                    for i, item in zip(range(len(strs)), strs[:len(strs) - 1]):
                        try:
                            channel = await client.get_entity(item)
                            if await client(LeaveChannelRequest(channel)):
                                res += '✅ترک کانال {}({}ام): موفق'.format(channel.title, i + 1) + '\n'
                                
                            remove_channel_id(channel.id)
                            
                        except ValueError:
                            res += '❌ترک کانال {}ام: ناموفق(کانالی با این نشانی برای ترک وجود ندارد)\n'.format(i + 1)
                        except TypeError:
                            res += '❌ترک کانال {}ام: ناموفق(برای ورودی فقط آدرس کانال را وارد کنید)\n'.format(i + 1)
                            
                await event.reply(res)
                
            elif re.findall(r'(?i)^/add_keywords', event.raw_text):
                for kw in strs[:len(strs) - 1]:
                    keywords.append(kw)
                await event.reply('✅کليد واژه های مورد نظر با موفقیت اضافه شد')
            elif re.findall(r'(?i)^/remove_keyword', event.raw_text):
                for kw in strs[:len(strs) - 1]:
                    keywords.remove(kw)
                await event.reply('✅کليد واژه های مورد نظر با موفقیت حذف شد')
            elif re.findall(r'(?i)^/channel_list', event.raw_text):
                lc = len(channels)
                if lc == 0:
                    await event.reply('لیست کانال های مورد بررسی خالی است')
                else:
                    try:
                        if lc <= 30:
                            await event.reply(' 🟢\n'.join([str(x[1]) + ': ' + str(x[2]) for x in channels]) + ' 🟢')
                        else:
                            for i in range(lc//30 + 1):
                                await event.reply(
                                    ' 🟢\n'.join([str(x[1]) + ': ' + str(x[2]) for x in
                                                  channels[30*i:30*(i+1) if 30*(i+1) <= lc else lc]])+' 🟢'
                                )
                    except telethon.errors.rpcerrorlist.FloodWaitError:
                        await event.reply('تلاش ناموفق، دوباره امتحان کنید')
                    except telethon.errors.FloodError:
                        await event.reply('تلاش ناموفق، دوباره امتحان کنید')
            elif re.findall(r'(?i)^/keywords_list', event.raw_text):
                if len(keywords) == 0:
                    await event.reply('لیست کلید واژه ها خالی است')
                else:
                    try:
                        async with client.action(chat, 'typing'):
                            await event.reply(' 🟢\n'.join([str(x) for x in keywords]) + ' 🟢')
                    except telethon.errors.FloodError:
                        await event.reply('تلاش ناموفق، دوباره امتحان کنید')
                        
            elif re.findall(r'(?i)^/set_mainchannel', event.raw_text):
                if len(strs) > 1:
                    channel = await client.get_entity(strs[1])
                    main_channel['id'] = channel.id
                    channel_forwards = channel.username
                    
                    await event.reply(f'آیدی {channel_forwards} با موفقیت تنظیم شد')
                
    except ChatIdInvalidError:
        pass
    except AttributeError:
        await event.reply('❗️access out of bounds🙂 \n'
                          '🚫شما در این محدوده مجاز به استفاده از دستورات نمی باشید. با تشکر')


@client.on(events.Album)
async def new_album_post(event):
    print(event)
    await client.forward_messages(main_group['id'], event.messages)


@client.on(events.NewMessage(forwards=False))
async def new_post(event):
    await post_analyser(event)


@client.on(events.MessageEdited(forwards=False))
async def new_edited_post(event):
    await post_analyser(event)


# check if post has not contain a given keywords and from channel that have been added
async def post_analyser(event):
    global channel_forwards
    try:
        ch = PeerChannel((await event.message.get_sender()).id)
        ch = await client.get_entity(ch)
        keyflag = True
        for i in keywords:
            if i in event.raw_text:
                keyflag = False
                break
        if not re.findall(r'(?i){}'.format(re.escape(channel_forwards)), event.raw_text):
            keyflag = False
        if f'{ch.id}' in channels and keyflag:
            await client.forward_messages(main_group['id'], event.message, as_album=True)
    except ValueError:
        pass


@client.on(events.NewMessage)
async def post_archives(event):
    global channel_forwards
    
    chat = await client.get_entity(PeerChat((await event.message.get_chat())).chat_id)
    if re.findall(r'(?i)^/accept', event.raw_text) and chat.id == main_group['id']:
        # get the date of last message, if now - date < 10min --> send with schedule
        lastmsgs = []
        channel = await client.get_entity(channel_forwards)
        async for item in client.iter_messages(main_channel['id'], scheduled=True):
            lastmsgs.append(item)
            break
        if len(lastmsgs) == 0:
            async for item in client.iter_messages(main_channel['id']):
                lastmsgs.append(item)
                break
        minutes_diff = (datetime.now(timezone.utc) - lastmsgs[0].date).total_seconds() // 60
        try:
            if minutes_diff >= 10:
                msg = await client.get_messages(chat, ids=event.reply_to_msg_id)
                if await client.forward_messages(main_channel['id'], msg):
                    await event.reply('ارسال با موفقیت انجام شد📤')
                    # await client.edit_message(chat, msg, '✔️این پست قبلا تایید گردیده است')
                    # await client.delete_messages(chat, msg)
            else:
                msg = await client.get_messages(chat, ids=event.reply_to_msg_id)
                if await client.forward_messages(main_channel['id'], msg, schedule=timedelta(minutes=10 - int(minutes_diff))):
                    await event.reply('✔️پست {} دقیقه دیگر ارسال می شود 📤'.format(10 - int(minutes_diff)))
                    # await client.ediِt_message(chat, msg, '✔️این پست قبلا تایید گردیده است')
                    # await client.delete_messages(chat, msg)
        except MessageAuthorRequiredError:
            pass
        except MessageIdInvalidError:
            pass
    elif re.findall(r'(?i)^/ignore', event.raw_text) and chat.id == main_group['id']:
        try:
            msg = await client.get_messages(chat, ids=event.reply_to_msg_id)
            await event.reply('عدم تایید 🛑 حذف پست انجام شد🗑')
            # await client.edit_message(chat, msg, '❌این پست قبلا حذف گردیده است📫')
            await client.delete_messages(chat, msg)
        except MessageAuthorRequiredError:
            pass
        except MessageIdInvalidError:
            pass

async def getChannels():
    global channel_forwards
    
    dialogs = client.iter_dialogs()
    subscribed_channels = []

    async for dialog in dialogs:
        if dialog.is_channel and not dialog.is_group:
            subscribed_channels.append((dialog.entity.id, dialog.entity.title,dialog.entity.username))

    print("Subscribed Channels:")
    for channel_id, channel_title,channel_uname in subscribed_channels:
        print(f"Channel ID: {channel_id}, Title: {channel_title}")
        if(channel_uname == "ssafum"):
            channel_forwards = channel_uname
            main_channel['id'] = channel_id
            
        save_channel_id(channel_id)
     

client.start(phone=os.environ.get("SSAFUM_phone" , "989939996761"))

client.loop.run_until_complete(getChannels())
channels = read_channel_ids()
    
client.run_until_disconnected()
