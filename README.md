# pyWeastCoastBot

This project is the python version of WeastCoastBot because my friends are picky and don't like nodejs

# Getting Started
## Requirements
* Docker


## Local Development

1. Create a `.env` file in `/bot` by copying `.env.example` and populating the variables with your values
2. Start up the app by running `docker-compose up --bulid`
   * this will run db migrations and hot reload for any code changes
3. Start coding!

### Adding a Cog
1. in `/bot/cogs` copy the cog template at `cog.py.example` and rename it to the command you'll be adding
2. Add a method that is named your command and annotate the method with `@commands.command()`
   * the parameters for this method will first be the discord context followed by command parameters

More info here - [Discord Cogs](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html)

### Troubleshooting

try a fresh build with
```
docker-compose down -v
docker-compose up --build
```