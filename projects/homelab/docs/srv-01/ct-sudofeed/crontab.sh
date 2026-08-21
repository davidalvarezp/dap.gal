# Edit this file to introduce tasks to be run by cron.
# 
# Each task to run has to be defined through a single line
# indicating with different fields when the task will be run
# and what command to run for the task
# 
# To define the time you can provide concrete values for
# minute (m), hour (h), day of month (dom), month (mon),
# and day of week (dow) or use '*' in these fields (for 'any').
# 
# Notice that tasks will be started based on the cron's system
# daemon's notion of time and timezones.
# 
# Output of the crontab jobs (including errors) is sent through
# email to the user the crontab file belongs to (unless redirected).
# 
# For example, you can run a backup of all your user accounts
# at 5 a.m every week with:
# 0 5 * * 1 tar -zcf /var/backups/home.tgz /home/
# 
# For more information see the manual pages of crontab(5) and cron(8)
# 
# m h  dom mon dow   command

#------BLOGGER------#
0 * * * * /usr/bin/python3 /opt/sudofeed-blogger/blogger_bot_7b.py >> /opt/sudofeed-blogger/blogger.log 2>&1

#------TELEGRAM------#
0 10 * * * python3 /opt/sudofeed/telegram_bot.py >> /opt/sudofeed/telegram.log 2>&1
0 11 * * * python3 /opt/sudofeed/telegram_bot.py >> /opt/sudofeed/telegram.log 2>&1
0 12 * * * python3 /opt/sudofeed/telegram_bot.py >> /opt/sudofeed/telegram.log 2>&1
0 13 * * * python3 /opt/sudofeed/telegram_bot.py >> /opt/sudofeed/telegram.log 2>&1
0 14 * * * python3 /opt/sudofeed/telegram_bot.py >> /opt/sudofeed/telegram.log 2>&1
0 19 * * * python3 /opt/sudofeed/telegram_bot.py >> /opt/sudofeed/telegram.log 2>&1
0 20 * * * python3 /opt/sudofeed/telegram_bot.py >> /opt/sudofeed/telegram.log 2>&1
0 21 * * * python3 /opt/sudofeed/telegram_bot.py >> /opt/sudofeed/telegram.log 2>&1
0 22 * * * python3 /opt/sudofeed/telegram_bot.py >> /opt/sudofeed/telegram.log 2>&1
0 23 * * * python3 /opt/sudofeed/telegram_bot.py >> /opt/sudofeed/telegram.log 2>&1

#------TWITTER------#
0 10 * * * python3 /opt/sudofeed/twitter_bot.py >> /opt/sudofeed/twitter.log 2>&1
0 12 * * * python3 /opt/sudofeed/twitter_bot.py >> /opt/sudofeed/twitter.log 2>&1
0 14 * * * python3 /opt/sudofeed/twitter_bot.py >> /opt/sudofeed/twitter.log 2>&1
0 19 * * * python3 /opt/sudofeed/twitter_bot.py >> /opt/sudofeed/twitter.log 2>&1
0 21 * * * python3 /opt/sudofeed/twitter_bot.py >> /opt/sudofeed/twitter.log 2>&1
