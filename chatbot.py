import ast, json, redis
from utils import weather_information, random_facts

class Chatbot:

    def __init__(self):
        '''
        Chatbot class that initializes the redis-pubsub based chatbot and handles user interaction with the chatbot.
        '''

        #  initiating redis client and pubsub
        self.client = redis.StrictRedis(host='redis', port=6379)
        self.pubsub = self.client.pubsub()

        # setting up variables
        
        ## decalring a variable to generate unique id for each user. checking if variable `user_counter` exists in db, if not then initializing it.
        if str(self.client.get("user_counter")) == "0":
            self.client.set("user_counter", 0)

        ## user identifiers
        self.username, self.user_id, self.name, self.age, self.gender, self.location = None, None, None, None, None, None

        ## global variables
        with open("./utils/introduction.txt", 'r') as f:
            self.introduction = f.read()

        with open("./utils/help.txt", 'r') as f:
            self.help = f.read()
    
    def introduce(self):
        '''
        Entry point of the code. This function asks users for their name and whether they want to continue entering more details and play with the chatbot.
        '''
        
        # preventing user input of their name to be an empty string.
        while not self.name:
            self.name = input("\nHi, please enter your name to get started: ").strip()

        # taking user input on whether they want to continue entering more details. the inputs are restricted to 'Y', 'y', 'N', 'n'.
        wish_to_continue = ""
        while wish_to_continue not in ["n", "y"]:
            wish_to_continue = input(f"\nHi {self.name}, just a few other details to get to know you better and before you can play around with the chatbot. Press 'Y' or 'y' to get started or 'N' or 'n' to exit: ").strip().lower()

        if wish_to_continue == "n":
            # terminating the chatbot if user doesn't want to continue.
            print(f"\nGoodBye, {self.name}!\n")
            return False
        else:
            # moving on to getting user information and then self (chatbot) introduction.
            self.identify()
            print(f"\n{self.introduction.format(self.name)}\n")

        return True
    
    def identify(self):
        '''
        This function asks user to input their details and then stores it in redis.
        '''

        # restricting input age to be a valid (integer or float) entry. 
        while not self.age:
            try:
                self.age = int(input(f"\nThanks for continuing, {self.name}, please enter your age: ", ).strip())
            except:
                print("\nInvalid entry; please only enter numerals.")

        # taking user's gender input
        while not self.gender:
            self.gender = input("\nNext, please enter your gender: ", ).strip()

        # taking user's location information and restricting the input to be a valid location by calling the weather api.
        while not self.location:
            self.location = input("\nLastly, please enter your city or state: ", ).strip()
            weather_update = weather_information.fetch(self.location)
            if 'Response' in weather_update.keys():
                # this is a hardcoded response in `weather_information.py` to know there was an error finding the city.
                print(f"\n{weather_update['Response']}")
                # setting `self.location` to None to not terminate the while loop and ask for the location again
                self.location = None
            else:
                # location's weather update successful.
                print(f"\nThanks! A quick weather update for your location ({self.location}) - Temperature: {weather_update['Temperature']} | Humidity: {weather_update['Humidity']}\n")

        # generating a unique identifier for each user basis the variable `user_counter` declared in redis above.
        self.user_id = self.client.incr("user_counter")
        # combining it with user's name to generate their username (again a unique identifier)
        self.username = str(str(self.name) + str(self.user_id))
        # adding user details to redis
        self.client.hset(
            f"users:{self.username}",
            mapping={
                "id": self.user_id,
                "name": self.name,
                "age": self.age,
                "gender": self.gender,
                "location": self.location
            }
        )

        return None
        

    def join_channel(self, channel, is_dm):
        '''
        This function lets users join a channel.
        '''

        # checking if channel is a direct-message (is_dm=True) or a broadcast (is_dm=False) and then setting the final name of the channel `channel_name` as stored in redis.
        if is_dm:
            channel_name = f"user_dm:{channel.strip()}"
        else:
            channel_name = f"channel:{channel.strip()}"

        # checking if user is already subscribed to the channel or not.
        if self.client.sismember(f"channels:{self.username}", channel_name) == 1:
            # nothing happens since already subscribed.
            print(f"\nYou are already subscribed to {channel}.\n")
        else:
            # subscribing user to the input channel.
            self.pubsub.subscribe(channel_name)
            # adding the channel name to user's unique set for list of channel they are subscribed to.
            self.client.sadd(f"channels:{self.username}", channel_name)
            # printing only when the channel is not a direct-message because all the users are by-default subscribed to their direct-message.
            if not is_dm:
                print(f"\nYou are now subscribed to {channel}.\n")

        return None

    def leave_channel(self, channel):
        '''
        This function lets users to leave a channel.
        '''

        # default channel name as it cannot be a direct-message.
        channel_name = f"channel:{channel.strip()}"
        
        # checking if user is subscribed to the channel.
        if self.client.sismember(f"channels:{self.username}", channel_name) == 1:
            # unsubscribing to the channel.
            self.pubsub.unsubscribe(channel_name)
            # removing it from user's unique set of subscribed channels.
            self.client.srem(f"channels:{self.username}", channel_name)
            print(f"\nYou are no longer subscribed to {channel}.\n")
        else:
            # no action needed.
            print(f"\nNo action needed as you were not subscribed to {channel}.\n")
        return None

    def send_message(self, channel, message, is_dm):
        '''
        This function lets users send a direct-message or a broadcast to a channel.
        '''
        
        # checking if channel is a direct-message (is_dm=True) or a broadcast (is_dm=False) and then setting the final name of the channel `channel_name` as stored in redis.
        if is_dm:
            channel_name = f"user_dm:{channel.strip()}"
        else:
            channel_name = f"channel:{channel.strip()}"

        # publishing the message
        self.client.publish(channel_name, message)
        if is_dm:
            print("\nYour message has been sent.\n")
        else:
            print("\nYour message has been published.\n")
        return None

    def read_message(self):
        '''
        This function fetches all the unread messages from direct-message or channels and delivers them to the user.
        '''

        # running a while true loop that breaks when no new messages are received.
        while True:
            # fetching a new message - one at a time.
            new_message = self.pubsub.get_message()
            # verifying the new message contains required information and filtering only for 'message' type updates.
            if type(new_message) == dict and new_message.get('type', None) == 'message':
                # is message a broadcast (`message_on.startswith()` == "channel:") or a direct-message (`message_on.startswith()` == "user_dm:")
                message_on = new_message.get('channel', b'').decode('utf-8')

                if message_on.startswith("user_dm:"):
                    # fetching custom data and converting it to dictionary to deliver it to the user.
                    data = ast.literal_eval(new_message['data'].decode('utf-8'))
                    print(f"\n[FROM: {data['from']}]: {data['message']}\n")

                elif message_on.startswith("channel:"):
                    # fetching data and delivering it to the user.
                    print(f"\n[ON: {message_on.replace('channel:', ''.strip())}]: {new_message['data'].decode('utf-8')}\n")
            else:
                # printing an end message when all messages read or no new messages of the desired type.
                print("\n=========END=========\n")
                break

        return None


    def send_direct_message(self, receiver_id):
        '''
        This function lets users send a direct message to their knowns using the receiver's username.
        '''
        
        # preveting note-to-self kind of situations.
        if receiver_id.strip() == self.username:
            print("\nYou cannot send a direct-message to yourself.\n")
            return None

        # fetching details of the receiver from redis.
        receiver = self.client.hgetall(f"users:{receiver_id.strip()}")
        if receiver != {}:
            # checking if `receiver` has desired format and fields. if yes, then asking for input message.
            message = input("\nUser found. Please enter your message: ")
            # send message
            self.send_message(channel=receiver_id.strip(), message=json.dumps({"from": self.username, "message": message}), is_dm=True)
        else:
            # return with a message for the sender to enter a correct username.
            print(f"\nNo user found. Please try again with a correct username.\n")
        
        return None

    def process_commands(self, user_input):
        '''
        This function processes all the input by the user and calls the target function.
        '''
        
        if user_input == "!help":
            # print help guide for the user
            print(f"\n{self.help.format(self.name)}\n")
            return None
        
        elif user_input.startswith("!weather"):
            # get weather update for the user.
            # checking if user entered a location. if not then using their own location
            user_input_location = user_input.replace("!weather", "").strip()
            if user_input_location == "":
                user_input_location = self.location

            # getting weather update
            weather_update = weather_information.fetch(user_input_location)
            if 'Response' in weather_update.keys():
                # this is a hardcoded response in `weather_information.py` to know there was an error finding the city.
                print(f"\n{weather_update['Response']}\n")
            else:
                # fetch successful.
                print(f"\n{user_input_location} - Temperature: {weather_update['Temperature']} | Humidity: {weather_update['Humidity']}\n")

            return None
        
        elif user_input == "!fact":
            # generate a random fact for the user.
            print(f"\nDo You Know? {random_facts.fetch()}\n")
            return None
        
        elif user_input == "!whoami":
            # fetch user information from redis and present it in a plain-english sentence.
            user_information = self.client.hgetall(f"users:{self.username}")
            print(f"\nYou are {user_information[b'name'].decode('utf-8')}. You are a {user_information[b'age'].decode('utf-8')}-year-old {user_information[b'gender'].decode('utf-8')} from {user_information[b'location'].decode('utf-8')}. Your username is {self.username}.\n")
            return None

        elif user_input.startswith("~listen"):
            # subscribe user to a channel given they have entered channel's name. if not, nothing happens and a message is printed asking the same.
            channel_name = user_input.replace("~listen", "").strip()
            if channel_name:
                self.join_channel(channel=channel_name, is_dm=False)
            else:
                print("\nPlease try again along with a channel name.\n")

            return None

        elif user_input.startswith("~publish"):
            # letting user broadcasting to a channel given they have entered channel's name. if not, nothing happens and a message is printed asking the same.
            channel_name = user_input.replace("~publish", "").strip()
            if channel_name:
                message = input("\nPlease enter your message: ")
                self.send_message(channel=channel_name, message=message, is_dm=False)
            else:
                print("\nPlease try again along with a channel name.\n")

            return None
        
        elif user_input.startswith("~leave"):
            # allows user to leave a channel given they have entered channel's name. if not, nothing happens and a message is printed asking the same.
            channel_name = user_input.replace("~leave", "").strip()
            if channel_name:
                self.leave_channel(channel=channel_name)
            else:
                print("\nPlease try again along with a channel name.\n")

            return None

        elif user_input == "~fetch":
            # print all unread direct-message and broadcast for the user.
            self.read_message()
            return None
                
        elif user_input.startswith("~dm"):
            # letting user send a direct-message given they have entered receiver's username. if not, nothing happens and a message is printed asking the same.
            receiver_id = user_input.replace("~dm", "").strip()
            if receiver_id:
                self.send_direct_message(receiver_id=receiver_id)
            else:
                print("\nPlease try again along with receiver's username.\n")

            return None

        else:
            # a message for user they have entered an incorect command and asking them to refer to help guide for list of valid commands.
            print(f"\nSorry, I did not understand that. {self.name}, please type [!help] to get list of all the valid commands.\n")
            return None
        

    def main(self):
        '''
        This function is the main loop of the chatbot.
        '''

        # getting to know the user and introducting the bot. if user wish continue, the output of `bot.introduce()` will be True and code will run.
        if bot.introduce():

            # subscribing to the self channel to receive direct messages.
            self.join_channel(channel=self.username, is_dm=True)

            while True:
                # taking input of user commands
                user_input = input("=>>")
                if user_input == "@Exit":
                    # user enters '@Exit', exitting with a goodbye message.
                    print(f"\nGoodBye, {self.name}\n")
                    break
                else:
                    # calling `process_commands` function for all other inputs
                    self.process_commands(user_input=user_input)

        return None

if __name__ == "__main__":
    # initializing Chatbot instance
    bot = Chatbot()
    # calling main function that handles all the functionalities of the chatbot.
    bot.main()