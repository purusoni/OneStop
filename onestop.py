# OneStop | Made by Puru Soni 

import _md5
import datetime
import string
import winsound
from functools import partial
import random
import mysql.connector
from captcha.image import ImageCaptcha
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from win10toast import ToastNotifier

MySQL_HOST = 'localhost'
MySQL_USER = 'root'
MySQL_PASSWORD = 'purusoni'
MySQL_DB = 'onestop_db'
count = 0

mydb = mysql.connector.connect(
    host=MySQL_HOST,
    user=MySQL_USER,
    passwd=MySQL_PASSWORD)

# create a cursor and create a database
my_cursor = mydb.cursor()
my_cursor.execute("CREATE DATABASE IF NOT EXISTS onestop_db")
mydb.commit()
mydb.close()


class LoginWindow(Screen):
    # add md5 hashes of default username and password to the credentials table
    def __init__(self, **kwargs):
        super(LoginWindow, self).__init__(**kwargs)
        self.captcha_source = None
        self.captcha_text = None
        self.username = None
        self.entered_password = None
        self.entered_username = None
        self.password = None

        self.mydb = mysql.connector.connect(
            host=MySQL_HOST,
            user=MySQL_USER,
            passwd=MySQL_PASSWORD,
            database=MySQL_DB, )

        self.mycursor = self.mydb.cursor()

        # create table if it doesn't exist
        self.mycursor.execute("CREATE TABLE IF NOT EXISTS credentials (username VARCHAR(255), password VARCHAR(255))")

        self.mycursor.execute("SELECT * FROM credentials")
        self.myresult = self.mycursor.fetchall()

        if len(self.myresult) == 0:
            self.mycursor.execute(
                "INSERT INTO credentials (username, password) VALUES ('6ad14ba9986e3615423dfca256d04e3f', '482c811da5d5b4bc6d497ffa98491e38')")

        self.mydb.commit()

    def generate_captcha(self):
        image = ImageCaptcha(width=300, height=50)
        captcha_text = ''.join(random.sample(string.ascii_uppercase + string.digits, random.randint(4, 6)))
        image.write(captcha_text, 'captcha.png')

        return captcha_text

    def login(self):
        # md5 the inputed username and password
        self.entered_username = _md5.md5(self.ids.username.text.encode()).hexdigest()
        self.entered_password = _md5.md5(self.ids.password.text.encode()).hexdigest()

        # check if the inputed username and password match the default username and password
        if self.entered_username == self.username and self.entered_password == self.password and self.ids.captcha_text.text == self.captcha_text:
            self.manager.current = 'mainW'
        else:
            self.ids.login_label.text = '\nInvalid username, password or captcha'.upper()
            self.ids.username.text = ''
            self.ids.password.text = ''
            self.ids.captcha_text.text = ''
            self.captcha_text = self.generate_captcha()
            self.ids.captcha_image.reload()
            self.ids.username.focus = True

    def on_pre_enter(self, *args):
        self.mycursor.execute("SELECT * FROM credentials")
        self.myresult = self.mycursor.fetchall()

        # extract username and password from the credentials table
        self.username = self.myresult[0][0]
        self.password = self.myresult[0][1]

        global count
        if count == 0:
            self.captcha_text = self.generate_captcha()
            count += 1


class MainWindow(Screen):
    pass


class PasswordManagerWindow(Screen):
    def __init__(self, **kwargs):
        super(PasswordManagerWindow, self).__init__(**kwargs)
        self.mydb = mysql.connector.connect(
            host=MySQL_HOST,
            user=MySQL_USER,
            passwd=MySQL_PASSWORD,
            database=MySQL_DB)

        self.cursor = self.mydb.cursor()
        self.cursor.execute(
            "Create table if not exists password_manager(id int(11) auto_increment primary key, "
            "site varchar(55), username varchar(55), password varchar(55))")
        self.mydb.commit()

    def add_password(self):
        site = self.ids.PMW_add_site.text
        username = self.ids.PMW_add_username.text
        password = self.ids.PMW_add_password.text

        # check if the site, username and password are not empty
        if site != '' and username != '' and password != '':
            self.cursor.execute("Insert into password_manager(site, username, password) values(%s, %s, %s)",
                                (site, username, password))
            self.mydb.commit()
            self.ids.PMW_add_label.text = '[font=candara]Password added[/font]'
        else:
            self.ids.PMW_add_label.text = '[font=candara]Please fill in all the fields[/font]'

        self.ids.PMW_add_site.text = ''
        self.ids.PMW_add_username.text = ''
        self.ids.PMW_add_password.text = ''

        self.view_passwords()



    def on_pre_enter(self, *args):
        self.cursor.execute("Select * from password_manager")
        data = self.cursor.fetchall()

        self.ids.PMW_view_label.text = '[font=candara][size=64]All Passwords[/size][/font]\n\n'

        if data:
            count = 1
            for row in data:
                line = f"{count}. Site: " + row[1] + "   Username: " + row[2] + "   Password: " + row[3]
                self.ids.PMW_view_label.text += line + "\n\n"
                count += 1
        else:
            self.ids.PMW_view_label.text = "No passwords found"

    def view_passwords(self):
        self.cursor.execute("Select * from password_manager")
        data = self.cursor.fetchall()

        self.ids.PMW_view_label.text = '[font=candara][size=64]All Passwords[/size][/font]\n\n'

        if data:
            count = 1
            for row in data:
                line = f"{count}. Site: " + row[1] + "   Username: " + row[2] + "   Password: " + row[3]
                self.ids.PMW_view_label.text += line + "\n"
                count += 1
        else:
            self.ids.PMW_view_label.text = "No passwords found"

    def search_passwords(self):
        self.ids.PMW_search_label.text = '[font=candara][b][size=28]Search results[/size][/b][/font]\n\n'

        if self.ids.PMW_search_site.text != '':
            site = self.ids.PMW_search_site.text
            self.cursor.execute("Select * from password_manager where site = %s", (site,))
            data = self.cursor.fetchall()

            for row in data:
                line = "Site: " + row[1] + "   Username: " + row[2] + "   Password: " + row[3]
                self.ids.PMW_search_label.text += line + "\n"

        if self.ids.PMW_search_username.text != '':
            username = self.ids.PMW_search_username.text
            self.cursor.execute("Select * from password_manager where username = %s", (username,))
            data = self.cursor.fetchall()

            for row in data:
                line = "Site: " + row[1] + "   Username: " + row[2] + "   Password: " + row[3]
                self.ids.PMW_search_label.text += line + "\n"

        if self.ids.PMW_search_password.text != '':
            password = self.ids.PMW_search_password.text
            self.cursor.execute("Select * from password_manager where password = %s", (password,))
            data = self.cursor.fetchall()

            for row in data:
                line = "Site: " + row[1] + "   Username: " + row[2] + "   Password: " + row[3]
                self.ids.PMW_search_label.text += line + "\n"

        if self.ids.PMW_search_site.text == '' and self.ids.PMW_search_username.text == '' and self.ids.PMW_search_password.text == '':
            self.ids.PMW_search_label.text = '[font=candara][size=54]Please enter a search term[/size][/font]'

        if self.ids.PMW_search_label.text == '[font=candara][b][size=28]Search results[/size][/b][/font]\n\n':
            self.ids.PMW_search_label.text = '[font=candara][size=54]No results found[/size][/font]'

        self.ids.PMW_search_site.text = ''
        self.ids.PMW_search_username.text = ''
        self.ids.PMW_search_password.text = ''

    # update username and passwords based on site name
    def update_passwords(self):
        site = self.ids.PMW_update_site.text
        username = self.ids.PMW_update_username.text
        password = self.ids.PMW_update_password.text

        self.cursor.execute("Update password_manager set username = %s, password = %s where site = %s",
                            (username, password, site))
        self.mydb.commit()

        self.ids.PMW_update_site.text = ''
        self.ids.PMW_update_username.text = ''
        self.ids.PMW_update_password.text = ''

        self.ids.PMW_update_label.text = '[font=candara][size=54]Updated[/size][/font]'

        self.view_passwords()


    def delete_passwords(self):
        site = self.ids.PMW_delete_site.text

        self.cursor.execute("Delete from password_manager where site = %s", (site,))
        self.mydb.commit()

        self.ids.PMW_delete_site.text = ''
        self.ids.PMW_delete_label.text = '[font=candara][size=50]Deleted[/size][/font]'

        self.view_passwords()


    def pmw_back(self):
        # clear all the labels
        self.ids.PMW_add_label.text = ''
        self.ids.PMW_view_label.text = ''
        self.ids.PMW_search_label.text = ''
        self.ids.PMW_update_label.text = ''
        self.ids.PMW_delete_label.text = ''

        self.manager.current = 'mainW'


class AlarmAndReminderWindow(Screen):
    def __init__(self, **kwargs):
        super(AlarmAndReminderWindow, self).__init__(**kwargs)
        self.message = None
        self.remaining_time = None
        self.timer_message = None

    # set an alarm
    def set_alarm(self):
        hour = self.ids.AARW_hour.text
        minute = self.ids.AARW_minute.text
        self.message = self.ids.AARW_message.text

        # check if the time is not valid
        if hour == '' or minute == '':
            self.ids.AARW_alarm_label.text = '[font=candara][size=50]Invalid Time[/size][/font]'
            return

        # convert field to 2 digits
        if len(hour) == 1:
            hour = '0' + hour
        if len(minute) == 1:
            minute = '0' + minute

        # convert time into seconds
        entered_time = int(hour) * 3600 + int(minute) * 60

        # get current time in seconds
        current_time = datetime.datetime.now()
        current_time = current_time.hour * 3600 + current_time.minute * 60 + current_time.second

        # check if time is in the future
        if entered_time > current_time:
            # set alarm using the time in seconds
            remaining_time = entered_time - current_time

            self.ids.AARW_alarm_label.text = f'Alarm will go off at {hour}:{minute}'

            # clear the text fields
            self.ids.AARW_hour.text = ''
            self.ids.AARW_minute.text = ''
            self.ids.AARW_message.text = ''

            # sleep for the time in seconds
            Clock.schedule_once(partial(self.alarm_ring, self), remaining_time)

        else:
            self.ids.AARW_alarm_label.text = 'Please enter a time in the future'

    def alarm_ring(self, instance, dt):
        # display message using toast
        notifier = ToastNotifier()
        notifier.show_toast(f'OneStop | Notification: ', self.message, duration=5)
        self.ids.AARW_alarm_label.text = 'Alarm went off'

        # play a sound using winsound
        winsound.Beep(1000, 500)
        winsound.Beep(500, 500)
        winsound.Beep(1000, 500)
        winsound.Beep(1000, 500)
        winsound.Beep(500, 500)
        winsound.Beep(1000, 500)


    # set a reminder
    def set_timer(self):
        hour = self.ids.AARW_timer_hour.text
        minute = self.ids.AARW_timer_minute.text
        second = self.ids.AARW_timer_second.text
        self.timer_message = self.ids.AARW_timer_message.text

        # check if the time is not valid
        if hour == '' or minute == '' or second == '':
            self.ids.AARW_timer_label.text = '[font=candara][size=50]Invalid Time[/size][/font]'
            return

        # convert fields to 2 digits
        if len(hour) == 1:
            hour = '0' + hour
        if len(minute) == 1:
            minute = '0' + minute
        if len(second) == 1:
            second = '0' + second

        # convert time into seconds
        self.remaining_time = int(hour) * 3600 + int(minute) * 60 + int(second)

        # clear the text fields
        self.ids.AARW_timer_hour.text = ''
        self.ids.AARW_timer_minute.text = ''
        self.ids.AARW_timer_second.text = ''
        self.ids.AARW_timer_message.text = ''

        self.ids.AARW_timer_label.text = f'Timer will go off in {hour} hours {minute} minutes and {second} seconds'

        # sleep for the time in seconds
        self.TimerClock = Clock.schedule_interval(partial(self.reminder_ring, self), 1)

    def reminder_ring(self, instance, dt):
        # display message using toast
        self.remaining_time -= 1

        if self.remaining_time <= 0:
            self.ids.AARW_timer_label.text = '[size=32]Timer went off[/size]'
            notifier = ToastNotifier()
            notifier.show_toast(f'OneStop | Notification: ', self.timer_message, duration=5)
            self.remaining_time = None
            Clock.unschedule(self.TimerClock)
        else:
            self.ids.AARW_timer_label.text = f'Timer will go off in {self.remaining_time // 3600} hours {self.remaining_time // 60 % 60} minutes and {self.remaining_time % 60} seconds'

    def aarw_back(self):
        # clear all the labels
        self.ids.AARW_alarm_label.text = 'Set an alarm'
        self.ids.AARW_timer_label.text = 'Set a timer'

        self.manager.current = 'mainW'


# create a scree for setting reminders (on basis of date)
class ReminderWindow(Screen):
    def __init__(self, **kwargs):
        super(ReminderWindow, self).__init__(**kwargs)
        self.mydb = mysql.connector.connect(host=MySQL_HOST, user=MySQL_USER, passwd=MySQL_PASSWORD, database=MySQL_DB)
        self.cursor = self.mydb.cursor()

        # create table if it doesn't exist
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS reminder (id INT AUTO_INCREMENT PRIMARY KEY, date VARCHAR(255), message VARCHAR(255))")
        self.mydb.commit()

    def set_reminder(self):
        day = self.ids.RW_day.text
        month = self.ids.RW_month.text
        year = self.ids.RW_year.text
        message = self.ids.RW_message.text

        # check if the date is not valid
        if day == '' or month == '' or year == '':
            self.ids.RW_set_label.text = '[font=candara][size=54]Invalid Date[/size][/font]'
            return

        # make all the values two digits
        if len(day) == 1:
            day = '0' + day
        if len(month) == 1:
            month = '0' + month
        if len(year) == 2:
            year = '20' + year

        # add date and message to the database (year-month-day)
        self.cursor.execute("Insert into reminder (date, message) values (%s, %s)", (f'{year}-{month}-{day}', message))

        self.ids.RW_set_label.text = '[font=candara][size=54]Reminder/Task set[/size][/font]'
        self.ids.RW_day.text = ''
        self.ids.RW_month.text = ''
        self.ids.RW_year.text = ''
        self.ids.RW_message.text = ''

        self.mydb.commit()

        self.refresh_all_reminders()
        self.refresh_today_reminders()

    def refresh_today_reminders(self):
        # get current date
        today = datetime.datetime.now()
        today = today.strftime('%Y-%m-%d')

        # get all reminders for today
        self.cursor.execute("Select * from reminder where date = %s", (today,))
        result = self.cursor.fetchall()

        # display all reminders
        self.ids.RW_today_label.text = ''

        for row in result:
            self.ids.RW_today_label.text += f'>> {row[2]}\n\n'

    def refresh_all_reminders(self):
        # get all reminders
        self.cursor.execute("Select * from reminder")
        result = self.cursor.fetchall()

        # display all reminders
        self.ids.RW_all_label.text = ""
        for row in result:
            self.ids.RW_all_label.text += f'>> {row[2]}\n\n'

    def on_pre_enter(self, *args):
        self.refresh_today_reminders()
        self.refresh_all_reminders()
        self.ids.RW_delete_label.text = "[font=candara][size=54]      Delete Reminders/Tasks\nbased on Date and/or Message"

    def delete_reminder(self):
        # delete reminders according to date and message
        if self.ids.RW_delete_date.text != '' and self.ids.RW_delete_message.text != '':
            self.cursor.execute("Delete from reminder where date = %s and message = %s",
                                (self.ids.RW_delete_date.text, self.ids.RW_delete_message.text))
            self.ids.RW_delete_label.text = '[font=candara][size=54]Reminder/tasks deleted[/size][/font]'
        elif self.ids.RW_delete_date.text != '':
            self.cursor.execute("Delete from reminder where date = %s", (self.ids.RW_delete_date.text,))
            self.ids.RW_delete_label.text = '[font=candara][size=54]Reminders/tasks deleted[/size][/font]'
        elif self.ids.RW_delete_message.text != '':
            self.cursor.execute("Delete from reminder where message = %s", (self.ids.RW_delete_message.text,))
            self.ids.RW_delete_label.text = '[font=candara][size=54]Reminders/tasks deleted[/size][/font]'
        elif self.ids.RW_delete_date.text == '' and self.ids.RW_delete_message.text == '':
            self.ids.RW_delete_label.text = '[font=candara][size=42]Please enter a date or message[/size][/font]'

        self.ids.RW_delete_date.text = ''
        self.ids.RW_delete_message.text = ''

        self.mydb.commit()

        self.refresh_all_reminders()
        self.refresh_today_reminders()

    def remW_back(self):
        # clear all the labels
        self.ids.RW_set_label.text = ''
        self.ids.RW_today_label.text = ''
        self.ids.RW_all_label.text = ''
        self.ids.RW_delete_label.text = ''

        self.manager.current = 'mainW'


# add a pomodoro timer
class PomodoroWindow(Screen):
    def __init__(self, **kwargs):
        super(PomodoroWindow, self).__init__(**kwargs)
        self.bt = None
        self.ft = None
        self.break_seconds = None
        self.focus_seconds = None
        self.mydb = mysql.connector.connect(host=MySQL_HOST, user=MySQL_USER, passwd=MySQL_PASSWORD, database=MySQL_DB)
        self.cursor = self.mydb.cursor()
        self.focus_time = 25
        self.break_time = 5

        # create table to store focus time and break time if it doesn't exist
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS pomodoro (id INT AUTO_INCREMENT PRIMARY KEY, focus_time INT, break_time INT)")

        # get focus and break time from database
        self.cursor.execute("Select * from pomodoro")
        result = self.cursor.fetchall()
        # if there is no record in the database, set focus time to 25 and break time to 5
        if len(result) == 0:
            self.cursor.execute("Insert into pomodoro (focus_time, break_time) values (%s, %s)",
                                (self.focus_time, self.break_time))
            self.mydb.commit()
        else:
            # extract focus and break time from results
            self.focus_time = result[0][1]
            self.break_time = result[0][2]

        # set current state
        self.state = 'focus'

    def start_pomodoro(self):

        self.focus_seconds = self.focus_time * 60
        self.break_seconds = self.break_time * 60

        if self.state == 'focus':
            # start focus timer and keep updating the pomodoro label every second using kivy clock
            self.ft = Clock.schedule_interval(partial(self.update_focus_timer, self), 1)

        elif self.state == 'break':
            # start break timer and keep updating the pomodoro label every second using kivy clock
            self.bt = Clock.schedule_interval(partial(self.update_break_timer, self), 1)

    def update_focus_timer(self, instance, dt):
        # update focus timer
        self.focus_seconds -= 1
        minutes = self.focus_seconds // 60
        seconds = self.focus_seconds % 60

        # convert time fields to 2 digits
        if minutes < 10:
            minutes = '0' + str(minutes)
        if seconds < 10:
            seconds = '0' + str(seconds)

        self.ids.pomodoro_label.text = f'[font=candara][size=44]Focus time left | {minutes}:{seconds}[/size][/font]'

        if self.focus_seconds <= 0:
            # stop focus timer
            self.ids.pomodoro_label.text = '[font=candara][size=54]Focus time finished[/size][/font]'
            winsound.Beep(1000, 500)
            winsound.Beep(500, 500)
            winsound.Beep(1000, 500)
            self.state = 'break'
            self.ft.cancel()
            self.start_pomodoro()

    def update_break_timer(self, instance, dt):
        # update break timer
        self.break_seconds -= 1

        minutes = self.break_seconds // 60
        seconds = self.break_seconds % 60

        # convert time fields to 2 digits
        if minutes < 10:
            minutes = '0' + str(minutes)
        if seconds < 10:
            seconds = '0' + str(seconds)

        self.ids.pomodoro_label.text = f'[font=candara][size=44]Break time left | {minutes}:{seconds}[/size][/font]'

        if self.break_seconds <= 0:
            # stop break timer
            self.ids.pomodoro_label.text = '[font=candara][size=54]Break time finished[/size][/font]'
            winsound.Beep(1000, 500)
            winsound.Beep(500, 500)
            winsound.Beep(1000, 500)
            self.state = 'focus'
            self.bt.cancel()
            self.start_pomodoro()

    def reset_pomodoro(self):
        # stop the pomodoro timer and reset the focus and break time
        if self.state == 'focus':
            self.ft.cancel()
            self.ids.pomodoro_label.text = '[font=candara][size=54]Pomodoro Timer[/size][/font]'
        elif self.state == 'break':
            self.bt.cancel()
            self.ids.pomodoro_label.text = '[font=candara][size=54]Pomodoro Timer[/size][/font]'
            self.state = 'focus'

    def set_pomodoro(self):
        # set focus and break time
        self.focus_time = int(self.ids.setting_focus_time.text)
        self.break_time = int(self.ids.setting_break_time.text)

        # update focus and break time in database
        self.cursor.execute("Update pomodoro set focus_time = %s, break_time = %s", (self.focus_time, self.break_time))
        self.mydb.commit()

        self.refresh_pomodoro()

        # clear focus and break time input fields
        self.ids.setting_focus_time.text = ''
        self.ids.setting_break_time.text = ''

        # update the setting_label
        self.ids.setting_label.text = '[font=candara][size=54]Settings saved[/size][/font]'

    def refresh_pomodoro(self):
        # update the pomodoro_focus_label and pomodoro_break_label
        self.ids.pomodoro_focus_label.text = f'[font=candara][size=28]Focus time: {self.focus_time} minutes[/size][/font]'
        self.ids.pomodoro_break_label.text = f'[font=candara][size=28]Break time: {self.break_time} minutes[/size][/font]'

    def on_pre_enter(self, *args):
        self.refresh_pomodoro()

    def pomodoro_back(self):
        # go back to the main page
        self.manager.current = 'mainW'


class WindowManager(ScreenManager):
    pass


kv = Builder.load_string("""
WindowManager:
    LoginWindow:
    MainWindow:
    PasswordManagerWindow:
    AlarmAndReminderWindow:
    ReminderWindow:
    PomodoroWindow:

<RoundedButton@Button>:
    markup: True
    background_color: (0,0,0,0)  # the last zero is the critical on, make invisible
    canvas.before:
        Color:
            rgba: (1,1,1,0.5) if self.state=='normal' else (0,.7,.7,1)  # visual feedback of press
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [17]

<TextInput>
    multiline: False
    background_color: (1,1,1, 0.7)
    font_size: self.height/1.7
    valign: 'middle'

<Label>
    markup: True

<TabbedPanel>
    tab_pos: 'left_mid'

<LoginWindow>:
    name: 'loginW'

    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height

        padding: 50
        spacing: 60

        Label:
            markup: True
            font_size: 32
            text: '[size=64][font=Impact][color=#5C00FF]OneStop[/font][/color] | Login[/size]'
            id: login_label
            size_hint: (1, 0.5)

        Label:
            text: '[i][font=candara]Made by Puru Soni[/font][/i]'
            font_size: 24
            color: (1,1,1,0.7)
            size_hint: (1, 0.1)

        GridLayout:
            padding: 20
            spacing: 10
            cols: 2

            Label:
                text: 'Username'
                font_size: 32
            TextInput:
                id: username
                multiline: False

            Label:
                text: 'Password'
                font_size: 32
            TextInput:
                id: password
                password: True
                multiline: False

            Image:
                source: 'captcha.png'
                id: captcha_image
            TextInput:
                id: captcha_text
                multiline: False

        RoundedButton:
            size_hint: (0.7, 0.2)
            pos_hint: {'center_x': 0.5}
            font_size: self.height/1.7
            text: 'Login'

            on_release: root.login()



<MainWindow>:
    name: 'mainW'
    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height

        Label:
            markup: True
            text: '[size=64][font=impact][color=#5C00FF]OneStop[/color][/font][/size]'
            size_hint: (1, 0.5)
        Label:
            text: '[font=candara]OneStop for multiple tasks[/font]'
            font_size: 44
            size_hint: (1, 0.1)
        Label:
            text: '[font=candara][i]Made by Puru Soni[/i][/font]'
            font_size: 24
            size_hint: (1, 0.6)

        GridLayout:
            cols: 2

            padding: 40
            spacing: 20

            RoundedButton:
                text: 'Password Manager'
                font_size: self.height/2.7
                on_release: app.root.current = 'passW'

            RoundedButton:
                text: 'Alarms & Timers'
                font_size: self.height/2.7
                on_release: app.root.current = 'aarW'

            RoundedButton:
                text: 'Reminders/Tasks'
                font_size: self.height/2.7
                on_release: app.root.current = 'remW'

            RoundedButton:
                text: 'Pomodoro Timer'
                font_size: self.height/2.7
                on_release: app.root.current = 'pomodoroW'



<PasswordManagerWindow>:
    name: 'passW'

    TabbedPanel:
        do_default_tab: False
        tab_width: root.height/5
        TabbedPanelItem:
            text: "Add"
            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20

                Label:
                    text:'[font=candara][b]Add A New Password[/b][/font]'
                    size_hint: (1, 0.5)
                    font_size: 64
                    id: PMW_add_label

                GridLayout:
                    cols: 2
                    spacing: 10
                    padding: 20

                    Label:
                        text: 'Site'
                        font_size: 32
                    TextInput:
                        id: PMW_add_site
                        multiline: False

                    Label:
                        text: 'Username'
                        font_size: 32
                    TextInput:
                        id: PMW_add_username
                        multiline: False

                    Label:
                        text: 'Password'
                        font_size: 32
                    TextInput:
                        id: PMW_add_password
                        multiline: False

                RoundedButton:
                    text: 'Add'
                    font_size: self.height/2
                    size_hint: (1, 0.2)
                    pos_hint: {'center_x': 0.5}
                    on_release: root.add_password()

                RoundedButton:
                    text: 'Back'
                    font_size: self.height/2
                    size_hint: (1, 0.2)
                    pos_hint: {'center_x': 0.5}
                    on_release: root.pmw_back()

        TabbedPanelItem:
            text: 'Show All'

            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 30

                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True

                    Label:
                        size_hint: (1, None)
                        height: self.texture_size[1]
                        text_size: self.width, None
                        padding: (10, 10)
                        id: PMW_view_label
                        markup: True
                        font_size: 28

                RoundedButton:
                    text: 'Back'
                    size_hint: (1, 0.1)
                    font_size: self.height/1.5
                    pos_hint: {'center_x': 0.5}
                    on_release: root.pmw_back()

        TabbedPanelItem:
            text: 'Search'

            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 10

                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True

                    Label:
                        size_hint: (1, None)
                        height: self.texture_size[1]
                        text_size: self.width, None
                        padding: (10, 10)
                        font_size: 20
                        id: PMW_search_label
                        text: "[font=candara][size=54]Search based on one (or more) of the following[/size][/font]"

                GridLayout:
                    cols: 2
                    spacing: 10
                    padding: 20

                    Label:
                        text: 'Site'
                        font_size: 28
                    TextInput:
                        id: PMW_search_site
                        multiline: False

                    Label:
                        text: 'Username'
                        font_size: 28
                    TextInput:
                        id: PMW_search_username
                        multiline: False

                    Label:
                        text: 'Password'
                        font_size: 28
                    TextInput:
                        id: PMW_search_password
                        multiline: False

                RoundedButton:
                    text: 'Search'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.search_passwords()

                RoundedButton:
                    text: 'Back'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.pmw_back()

        TabbedPanelItem:
            text: 'Update'

            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20

                Label:
                    id: PMW_update_label
                    text: '[font=candara][size=50]Update username and password[/size][/font]'

                GridLayout:
                    cols: 2
                    Label:
                        text: 'Enter site name to update'
                        font_size: 24
                    TextInput:
                        id: PMW_update_site

                    Label:
                        text: 'Enter NEW username'
                        font_size: 24
                    TextInput:
                        id: PMW_update_username

                    Label:
                        text: 'Enter NEW password'
                        font_size: 24
                    TextInput:
                        id: PMW_update_password


                RoundedButton:
                    text: 'Update'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.update_passwords()

                RoundedButton:
                    text: 'Back'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.pmw_back()

        TabbedPanelItem:
            text: 'Delete'

            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20

                Label:
                    id: PMW_delete_label
                    text: "[font=candara][size=50]Delete Passwords[/size][/font]"

                GridLayout:
                    cols: 2
                    size_hint: (1, 0.5)
                    padding: 40

                    Label:
                        text: 'Site: '
                        font_size: 32
                    TextInput:
                        id: PMW_delete_site
                        multiline: False

                RoundedButton:
                    text: 'Delete'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.delete_passwords()

                RoundedButton:
                    text: 'Back'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.pmw_back()


<AlarmAndReminderWindow>:
    name: 'aarW'

    TabbedPanel:
        do_default_tab: False
        tab_width: root.height/2

        TabbedPanelItem:
            text: "Alarm"
            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20
                Label:
                    id: AARW_alarm_label
                    font_size: 32
                    text: "[font=candara][size=54]Set Alarm[/size][/font]"
                    size_hint: (1, 0.5)

                GridLayout:
                    cols: 2
                    padding: 20
                    spacing: 10

                    Label:
                        text: "Hour (24-hour format)"
                        font_size: 30
                    TextInput:
                        id: AARW_hour
                        multiline: False
                    Label:
                        text: "Minute"
                        font_size: 30
                    TextInput:
                        id: AARW_minute
                        multiline: False
                    Label:
                        text: "Message"
                        font_size: 30
                    TextInput:
                        id: AARW_message
                        multiline: False
                RoundedButton:
                    text: "Set"
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.set_alarm()
                RoundedButton:
                    text: "Back"
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.aarw_back()

        TabbedPanelItem:
            text: "Timer"
            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20
                Label:
                    id: AARW_timer_label
                    text: "[font=candara][size=54]Set Timer[/size][/font]"
                    font_size: 28
                    size_hint: (1, 0.7)

                GridLayout:
                    cols: 2
                    padding: 20
                    spacing: 10

                    Label:
                        text: "Hours"
                        font_size: 30
                    TextInput:
                        id: AARW_timer_hour
                        multiline: False
                    Label:
                        text: "Minutes"
                        font_size: 30
                    TextInput:
                        id: AARW_timer_minute
                        multiline: False
                    Label:
                        text: "Seconds"
                        font_size: 30
                    TextInput:
                        id: AARW_timer_second
                        multiline: False
                    Label:
                        text: "Message"
                        font_size: 30
                    TextInput:
                        id: AARW_timer_message
                        multiline: False
                RoundedButton:
                    text: "Set"
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.set_timer()
                RoundedButton:
                    text: "Back"
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.aarw_back()


<ReminderWindow>:
    name: 'remW'

    TabbedPanel:
        do_default_tab: False
        tab_width: root.height/4

        TabbedPanelItem:
            text: "Today's"

            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20

                Label:
                    text: "[font=candara][size=54]Today's Reminders/Tasks[/size][/font]"
                    halign: 'center'
                    size_hint: (1, 0.7)

                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True

                    Label:
                        size_hint: (1, None)
                        height: self.texture_size[1]
                        text_size: self.width, None
                        padding: (10, 10)
                        font_size: 20
                        id: RW_today_label
                        text: "Press 'Refresh' to see today's reminders/tasks"

                RoundedButton:
                    text: 'Back'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.remW_back()

        TabbedPanelItem:
            text: "All"

            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20

                Label:
                    text: "[font=candara][size=54]All Reminders/Tasks[/size][/font]"
                    halign: 'center'
                    size_hint: (1, 0.7)

                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True

                    Label:
                        size_hint: (1, None)
                        height: self.texture_size[1]
                        text_size: self.width, None
                        padding: (10, 10)
                        font_size: 20
                        id: RW_all_label
                        text: "Press 'Refresh' to see refresh reminders/tasks"

                RoundedButton:
                    text: 'Back'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.remW_back()

        TabbedPanelItem:
            text: "Add"

            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20

                Label:
                    text: "[font=candara][size=50]Set Reminder[/size][/font]"
                    id: RW_set_label
                    size_hint: (1, 0.7)

                GridLayout:
                    cols: 2
                    padding: 20
                    spacing: 10

                    Label:
                        text: "Day"
                        font_size: 28
                    TextInput:
                        id: RW_day
                        multiline: False
                    Label:
                        text: "Month"
                        font_size: 28
                    TextInput:
                        id: RW_month
                        multiline: False
                    Label:
                        text: "Year"
                        font_size: 28
                    TextInput:
                        id: RW_year
                        multiline: False
                    Label:
                        text: "Message"
                        font_size: 28
                    TextInput:
                        id: RW_message
                        multiline: False
                RoundedButton:
                    text: "Set"
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.set_reminder()
                RoundedButton:
                    text: "Back"
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.remW_back()

        TabbedPanelItem:
            text: "Delete"

            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20

                Label:
                    text: "[font=candara][size=54]Delete Reminders/Tasks based on Date and/or Message"
                    id: RW_delete_label
                    size_hint: (1, 0.7)

                GridLayout:
                    cols: 2
                    padding: 20
                    spacing: 10

                    Label:
                        text: "Date (yyyy-mm-dd)"
                        font_size: 32
                    TextInput:
                        id: RW_delete_date
                        multiline: False
                    Label:
                        text: "Message"
                        font_size: 32
                    TextInput:
                        id: RW_delete_message
                        multiline: False
                RoundedButton:
                    text: "Delete"
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.delete_reminder()
                RoundedButton:
                    text: "Back"
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.remW_back()

<PomodoroWindow>:
    name: 'pomodoroW'

    TabbedPanel:
        do_default_tab: False
        tab_width: root.height/2
        TabbedPanelItem:
            text: 'Pomodoro'

            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20

                Label:
                    text: '[font=candara][size=54]Pomodoro Timer[/size][/font]'
                    size_hint: (1, 0.7)
                    id: pomodoro_label
                Label:
                    text: 'Focus Time: '
                    size_hint: (1, 0.3)
                    id: pomodoro_focus_label
                Label:
                    text: 'Short Break: '
                    size_hint: (1, 0.3)
                    id: pomodoro_break_label
                RoundedButton:
                    text: 'Start'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.start_pomodoro()
                RoundedButton:
                    text: 'Reset'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.reset_pomodoro()
                RoundedButton:
                    text: 'Back'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.pomodoro_back()

        TabbedPanelItem:
            text: 'Settings'

            BoxLayout:
                orientation: 'vertical'
                size: root.width, root.height
                padding: 40
                spacing: 20

                Label:
                    text: '[font=candara][size=54]Settings[/size][/font]'
                    id: setting_label
                    size_hint: (1, 0.7)

                GridLayout:
                    cols: 2
                    padding: 20
                    spacing: 10

                    Label:
                        text: 'Focus Time (minutes)'
                        font_size: 30
                    TextInput:
                        id: setting_focus_time
                        multiline: False

                    Label:
                        text: 'Short Break (minutes)'
                        font_size: 30
                    TextInput:
                        id: setting_break_time
                        multiline: False

                RoundedButton:
                    text: 'Set'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.set_pomodoro()
                RoundedButton:
                    text: 'Back'
                    size_hint: (1, 0.2)
                    font_size: self.height/1.7
                    on_release: root.pomodoro_back()

""")


class OneStopApp(App):
    def build(self):
        return kv


if __name__ == "__main__":
    OneStopApp().run()
