import os, episode, googlevoice
import config #configuration constants

SMS_CHAR_LIMIT = 160
RULER_WIDTH = 30

def sms_string(text):
    '''Shortens a string to fit in 160 characters'''

    sms = ''
    
    if len(text) > SMS_CHAR_LIMIT:
        sms = sms[:SMS_CHAR_LIMIT - 3] + '...'
    else:
        sms = text

    return sms

def send_sms(text, uname, passwd, phone):
    '''sends a text message via google voice'''
    
    #truncate texts longer than 169 char
    sms = sms_string(text)
    
    #send the SMS
    voice = googlevoice.Voice()
    voice.login(email=uname, passwd=passwd)        
    voice.send_sms(phone,sms)

def show_override(episode):
    '''overrides show names as needed'''

    renamed = False
    for pattern, show in config.renames.iteritems():

        if pattern in episode.show.lower() and show != episode.show:
            episode.show = show
            renamed = True
            break

    return renamed

def iter_episodes(root):
    '''find potential episodes in root and its subdirectories'''
    for dir, _, files in os.walk(root):
        for file in files:
            path = os.path.join(dir, file)

            try:
                yield episode.get_episode(path)
            except (episode.InvalidEpisode, IOError):
                continue

def find_dupes(episode):
    dest = iter_episodes(episode.episode_path(config.show_dir))
    return [ dest_ep for dest_ep in dest \
           if episode.episode == dest_ep.episode \
           and episode.file != dest_ep.file ]

def main():

    ep_list = []
    
    for ep in iter_episodes(config.dl_dir):

        if not ep.is_sample and ep.extension in config.extensions:
            print ep.file, "found."

            if show_override(ep):
                print "Overrided show to", ep.show

            copied = ep.put_file(config.show_dir)

            if copied:
                print "Episode copied."
                if ep.is_proper and config.delete_nukes:
                    print "Proper detected. Checking for nukes..."
                    for nuke in find_dupes(ep):
                        print "Removing nuke:", nuke.path
                        nuke.del_file()
                else:
                    ep_list.append(ep)

                if config.delete_files:
                    print "Removing staged file:", ep.path
                    ep.del_file()
            else:
                print "Nothing to copy."

            print '-' * RULER_WIDTH

    str_list = ", ".join([str(f) for f in ep_list])

    if str_list:
        text = 'New eps: ' + str_list
        print text
        send_sms(text, config.gv_uname, config.gv_pass, config.phone)

main()