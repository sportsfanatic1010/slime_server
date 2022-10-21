import asyncio, discord, shutil
from discord.ext import commands, tasks
from bot_files.backend_functions import server_command, format_args, server_status, lprint
from bot_files.components import dc_dict, new_buttons
import bot_files.backend_functions as backend
import slime_vars

start_button = [['Start Server', 'serverstart', '\U0001F680']]

class World_Backups(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['worldbackupslist', 'backuplist' 'backupslist', 'wbl'])
    async def worldbackups(self, ctx, amount=10):
        """
        Show world backups.

        Args:
            amount optional default(10): Number of most recent backups to show.

        Usage:
            ?saves
            ?saves 15
        """

        embed = discord.Embed(title='World Backups :floppy_disk:')
        worlds = backend.enum_dir(slime_vars.world_backups_path, 'd')
        if worlds is False:
            await ctx.send("No world backups found.")
            return False

        for backup in worlds[-amount:]:
            embed.add_field(name=backup[3], value=f"`{backup[0]}`", inline=False)
        await ctx.send(embed=embed)
        await ctx.send("Use `?worldrestore <index>` to restore world save.")

        await ctx.send("**WARNING:** Restore will overwrite current world. Make a backup using `?backup <codename>`.")
        lprint(ctx, f"Fetched {amount} world saves")

    @commands.command(aliases=['backupworld', 'newworldbackup', 'worldbackupnew', 'wbn'])
    async def worldbackup(self, ctx, *name):
        """
        new backup of current world.

        Args:
            name: Keywords or codename for new save. No quotes needed.

        Usage:
            ?backup everything not on fire
            ?backup Jan checkpoint
        """

        if not name:
            await ctx.send("Usage: `?worldbackup <name>`\nExample: `?worldbackup Before the reckoning`")
            return False
        name = format_args(name)

        await ctx.send("***Creating World Backup...*** :new::floppy_disk:")
        await server_command(f"save-all", discord_msg=False)
        await asyncio.sleep(3)
        new_backup = backend.new_backup(name, slime_vars.server_path + '/world', slime_vars.world_backups_path)
        if new_backup:
            await ctx.send(f"**New World Backup:** `{new_backup}`")
        else: await ctx.send("**ERROR:** Problem saving the world! || it's doomed!||")

        await ctx.invoke(self.bot.get_command('worldbackupslist'))
        lprint(ctx, "New world backup: " + new_backup)

        try: await ctx.invoke(self.bot.get_command('_update_server_panel'), 'world_backups')  # Updates panel if open
        except: pass

    @commands.command(aliases=['wbdate'])
    async def worldbackupdate(self, ctx):
        """Creates world backup with current date and time as name."""

        await ctx.invoke(self.bot.get_command('worldbackup'), '')

    @commands.command(aliases=['restoreworld', 'worldbackuprestore', 'wbr'])
    async def worldrestore(self, ctx, index='', now=''):
        """
        Restore a world backup.

        Args:
            index: Get index with ?worldbackups command.
            now optional: Skip 15s wait to stop server. E.g. ?restore 0 now

        Usage:
            ?restore 3
            ?wbr 5 now

        Note: This will not make a backup beforehand, suggest doing so with ?backup command.
        """

        if index == 'button':  # If this command triggered from a button.
            index = dc_dict('world_backup_selected')
        try: index = int(index)
        except:
            await ctx.send("Usage: `?worldrestore <index> [now]`\nExample: `?worldrestore 0 now`")
            return False

        fetched_restore = backend.get_from_index(slime_vars.world_backups_path, index, 'd')
        lprint(ctx, "World restoring to: " + fetched_restore)
        await ctx.send("***Restoring World...*** :floppy_disk::leftwards_arrow_with_hook:")
        if await server_command(f"say ---WARNING--- Initiating jump to save point in 5s! : {fetched_restore}"):
            await asyncio.sleep(5)
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        if not backend.restore_backup(fetched_restore, slime_vars.server_path + '/world'):
            await ctx.send(f"**Error:** Issue restoring world: {fetched_restore}")
            return False

        await ctx.send(f"**Restored World:** `{fetched_restore}`")
        await asyncio.sleep(5)

        await ctx.send("Start server with `?start` or click button", view=new_buttons(start_button))

    @commands.command(aliases=['deleteworld', 'wbd'])
    async def worldbackupdelete(self, ctx, index=''):
        """
        Delete a world backup.

        Args:
            index: Index number of the backup to delete. Get number with ?worldbackups command.

        Usage:
            ?delete 0
        """

        if index == 'button':  # If this command triggered from a button.
            index = dc_dict('world_backup_selected')
        try: index = int(index)
        except:
            await ctx.send("Usage: `?worldbackupdelete <index>`\nExample: `?wbd 1`")
            return False

        to_delete = backend.get_from_index(slime_vars.world_backups_path, index, 'd')
        if not backend.delete_dir(to_delete):
            await ctx.send(f"**Error:** Issue deleting: `{to_delete}`")
            return False

        await ctx.send(f"**World Backup Deleted:** `{to_delete}`")
        lprint(ctx, "Deleted world backup: " + to_delete)

        try: await ctx.invoke(self.bot.get_command('_update_server_panel'), 'world_backups')  # Updates panel if open
        except: pass

    @commands.command(aliases=['rebirth', 'hades', 'resetworld'])
    async def worldreset(self, ctx, now=''):
        """
        Deletes world save (does not touch other server files).

        Args:
            now optional: No 5s warning before resetting.

        Usage:
            ?worldreset
            ?hades now

        Note: This will not make a backup beforehand, suggest doing so with ?backup command.
        """

        await server_command("say ---WARNING--- Project Rebirth will commence in T-5s!", discord_msg=False)
        await ctx.send(":fire: **Project Rebirth Commencing** :fire:")
        await ctx.send("**NOTE:** Next launch may take longer.")

        if await server_status():
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        try:
            shutil.rmtree(slime_vars.server_path + '/world')
        except:
            await ctx.send("Error trying to reset world.")
            lprint(ctx, "ERROR: Issue deleting world folder.")
        finally:
            await ctx.send("**Finished.**")
            await ctx.send("You can now start the server with `?start`.")
            lprint(ctx, "World Reset")

class Server_Backups(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['serverbackupslist', 'sbl'])
    async def serverbackups(self, ctx, amount=10):
        """
        List server backups.

        Args:
            amount default(5): How many most recent backups to show.

        Usage:
            ?serversaves - Shows 10
            ?serversaves 15
        """

        embed = discord.Embed(title='Server Backups :floppy_disk:')
        servers = backend.enum_dir(slime_vars.server_backups_path)

        if servers is False:
            await ctx.send("No server backups found.")
            return False

        for save in servers[-amount:]:
            embed.add_field(name=save[3], value=f"`{save[0]}`", inline=False)
        await ctx.send(embed=embed)

        await ctx.send("Use `?serverrestore <index>` to restore server.")
        await ctx.send("**WARNING:** Restore will overwrite current server. Create backup using `?serverbackup <codename>`.")
        lprint(ctx, f"Fetched {amount} world backups")

    @commands.command(aliases=['backupserver', 'newserverbackup', 'serverbackupnew', 'sbn'])
    async def serverbackup(self, ctx, *name):
        """
        New backup of server files (not just world save).

        Args:
            name: Keyword or codename for save.

        Usage:
            ?serverbackup Dec checkpoint
        """

        if not name:
            await ctx.send("Usage: `?serverbackup <name>`\nExample: `?serverbackup Everything just dandy`")
            return False

        name = format_args(name)
        await ctx.send(f"***Creating Server Backup...*** :new::floppy_disk:")
        if await server_command(f"save-all", discord_msg=False):
            await asyncio.sleep(3)
        new_backup = backend.new_backup(name, slime_vars.server_path, slime_vars.server_backups_path)
        if new_backup:
            await ctx.send(f"**New Server Backup:** `{new_backup}`")
        else: await ctx.send("**ERROR:** Server backup failed! :interrobang:")

        await ctx.invoke(self.bot.get_command('serverbackupslist'))
        lprint(ctx, "New server backup: " + new_backup)

        try: await ctx.invoke(self.bot.get_command('_update_server_panel'), 'server_backups')  # Updates panel if open
        except: pass

    @commands.command(aliases=['sbdate'])
    async def serverbackupdate(self, ctx):
        """Creates server backup with current date and time as name."""

        await ctx.invoke(self.bot.get_command('serverbackup'), '')

    @commands.command(aliases=['restoreserver', 'serverbackuprestore', 'restoreserverbackup', 'sbr'])
    async def serverrestore(self, ctx, index='', now=''):
        """
        Restore server backup.

        Args:
            index: Number of the backup to restore. Get number from ?serversaves command.
            now optional: Stop server without 15s wait.

        Usage:
            ?serverrestore 0
            ?sbr 1 now
        """

        if index == 'button':  # If this command triggered from a button.
            index = dc_dict('server_backup_selected')
        try: index = int(index)
        except:
            await ctx.send("Usage: `?serverrestore <index> [now]`\nExample: `?serverrestore 2 now`")
            return False

        fetched_restore = backend.get_from_index(slime_vars.server_backups_path, index, 'd')
        lprint(ctx, "Server restoring to: " + fetched_restore)
        await ctx.send(f"***Restoring Server...*** :floppy_disk::leftwards_arrow_with_hook:")

        if await server_status():
            await server_command(f"say ---WARNING--- Initiating jump to save point in 5s! : {fetched_restore}")
            await asyncio.sleep(5)
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        if backend.restore_backup(fetched_restore, slime_vars.server_path):
            await ctx.send(f"**Server Restored:** `{fetched_restore}`")
        else: await ctx.send("**ERROR:** Could not restore server!")

        await ctx.send("Start server with `?start` or click button", view=new_buttons(start_button))

    @commands.command(aliases=['deleteserverrestore', 'serverdeletebackup', 'serverrestoredelete', 'sbd'])
    async def serverbackupdelete(self, ctx, index=''):
        """
        Delete a server backup.

        Args:
            index: Index of server save, get with ?serversaves command.

        Usage:
            ?serverbackupdelete 0
            ?sbd 5
        """

        if index == 'button':  # If this command triggered from a button.
            index = dc_dict('server_backup_selected')
        try: index = int(index)
        except:
            await ctx.send("Usage: `?serverbackupdelete <index>`\nExample: `?sbd 3`")
            return False

        to_delete = backend.get_from_index(slime_vars.server_backups_path, index, 'd')
        if not backend.delete_dir(to_delete):
            await ctx.send(f"**Error:** Issue deleting: `{to_delete}`")
            return False

        await ctx.send(f"**Server Backup Deleted:** `{to_delete}`")
        lprint(ctx, "Deleted server backup: " + to_delete)

        try: await ctx.invoke(self.bot.get_command('_update_server_panel'), 'server_backups')  # Updates panel if open
        except: pass

async def setup(bot):
    await bot.add_cog(World_Backups(bot))
    await bot.add_cog(Server_Backups(bot))