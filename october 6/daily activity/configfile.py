import configparser

config=configparser.ConfigParser()
config["Database"]={
    "host":"localhost",
    "port":"3306",
    "user":"root",
    "password":"admin",
}

with open("app.inl","w") as configfile:
    config.write(configfile)

config.read("app.inl")
print(config["Database"]["host"])