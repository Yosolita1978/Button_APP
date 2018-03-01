# Lyft #Dashbutton

I configured an AWS dashbutton that calls a Lyft ride to the address of my next google calendar event. I wrote a script that calls five APIs, maintaining the constraint of no written user input or output. To store my credentials for those APIs, I am using a DynamoDB and an AWS lambda function to configure the button.

![Image of Dashbutton](https://media.licdn.com/media/AAEAAQAAAAAAAApdAAAAJGE2MTgxNmFjLTdhZTItNGFmZS1iOGU5LWFhMGU1MGY2YWRlNA.jpg)

# How it works?

  - The button lives next to my door. 
  - I push the button
  - The physical push connects the button to my wifi and wakes up the lambda function with the sandbox context set up in false
  - The lambda function will call the script in python that lives in the serverless AWS
  - The script will go to my google calendar and check my next event and grab that address
  - The next function will grab that address and convert it to a tuple of longitude and latitude
  - The next API call will request a Lyft ride from my home to that point. 
  - The next API call will send me a Twilio notification with the result of the process
  - The script in the AWS server will go back to sleep. 

The script can also:
  - Import and save my different credentials in a DynamoDB
  - Request new tokens when a credential has expired
  - thanks to the AWS server, save some statics of use

#### Technologies

Python. All the calls to the different Apis are written in Python

### Structure

I'm using a number of APIs to work properly:

* Google Credential
* Google Calendar API
* Google Maps Requests
* Dynamodb (I'm using boto3 to work with the dynamoDB)
* Lyft API (I'm using the lyft_rides libraries to work with the Lyft API)
* Twilio API (I'm using the twilio.rest libraries to work with this API)

### Installation
All the dependencies are listed in requirements.txt.

#### Possible Improvements

This project was completed in under a month, so there are definitely areas for improvement. Specifically:

- Tests are needed
- Functionality for setting up the button from different "homes"
- Functionality for setting up differnts buttons.

#### Author
Hi! My name is [Cristina Rodriguez ](https://www.linkedin.com/in/crissrodriguez/), and I am a software engineer. I received training from Hackbright Academy, an engineering bootcamp for women in San Francisco  (graduation: March 2017). I used to work as a project manager for a software company, and there I got interested in learning Python and being able to create my software projects. I'm currently seeking a front-end developer role in the San Francisco Bay Area. If you have a role that I should hear about, feel free to email yosola at gmail.
