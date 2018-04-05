# Watchtower

**Watchtower** is a platform for social media listening and publishing. 

### Listening 
Watchtower collects 
- news (articles, blog posts ...)
- events 

and detects

- conversations (discussions, questions, observations ...)
- local commuities & influencers

related to a topic defined by the user by just providing a collection
of anchor keywords.

### Publising
All content is published through an API interface. 

News can be shared as a scheduled tweets.


## Getting Started

Watchtower is alive on [https://watchtower.openmaker.eu](https://watchtower.openmaker.eu). 

The following instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites
* Access tokens for Twitter, Reddit, Facebook, Eventbrite, Meetup. All these tokens are optional but in some cases you will miss some of the features of the platform.
* To manage system errors you need to provide a [sentry.io](https://sentry.io/) token.
* For publishing tweet, you must have a domain. This is mandatory otherwise you can not schedule tweets.

To deploy this project you need Docker and Docker-compose to be installed in your system.

#### For Ubuntu users
* [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1) 
* [Docker Compose](https://docs.docker.com/compose/install/#install-compose) 

#### For Mac users
* [Docker Stable Channel](https://docs.docker.com/docker-for-mac/install/) 

## Built With

* [Tornado](http://www.tornadoweb.org/en/stable/) - The web framework used
* [Docker](https://www.docker.com/) - Deployment tool


## Deployment

* Create an environment file from the example environment file. 

```$ cp .env-example .env```

* Modify .env file according to your configurations
* Run the following command to build server

```$ sudo bash deploy.sh```

Open your favourite browser and type [http://localhost:8484](http://localhost:8484)

## Run

* Run the following command to start server

```$ sudo bash run.sh```

Open your favourite browser and type [http://localhost:8484](http://localhost:8484)


## Authors

* **Enis Simsar** - *Initial work* - [enisimsar](https://github.com/enisimsar)
* **Kemal Berk Kocabağlı** - [berk94](https://github.com/berk94)
* **Barış Can Esmer** - [barisesmer](https://github.com/barisesmer)

See also the list of [contributors](https://github.com/enisimsar/WatchTower/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details



