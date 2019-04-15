# Web Forum to NodeBB

*A collection of Python scripts to help migrate online forums to Mongo for use with NodeBB*

> **Note: These scripts extract data from HTML web forums, not an existing database**

> **These scripts are very messy, well the below the quality I try to maintain when releasing source files.**  They've been thrown together for my particular problem, and I thought others might find something useful.  Beyond that, it doesn't seem worth the effort to clean and potentially re-write large portions.

## Overview

### Background

I recently had the problem of wanting to preserve an old internet message board on an aging web server, but I didn't want a static archive.  My goal was to migrate the forum to a new system, maintaining all existing data but supporting new posts and modern search features — a "living archive".

Unfortunately, I did not have access to the previous system's database.  This was a significant technical hurdle that ruled out any existing migration tools.  Ultimately, I hacked together this collection of scripts to crawl a web board and convert the data into a Mongo database for NodeBB.

[NodeBB](https://nodebb.org) is relatively new forum software, but it has a lot of nice features that set it apart from classic systems like myBB or phpBB.  It's flexible Mongo-based schema was the real selling point.  Generating the database programmatically can be done very easily... I expect it would take years of studying myBB's schema to get close to a working system!

### Caveats

Before discussing more, I want to detail the limitations right up front.

- My sample scripts were written for Invision's *IP.Board* forum software, circa 2005.  Forums powered by any other platform will very likely require changing the parsing scripts `html_to_files.py` and `files_to_fields.py`.  I expect the `Mongo`[^1] class in `Mongo.py` will work in any case because it deals more with NodeBB's schema.  It may take some experimenting with your HTML source, but as long as you can parse out *user*, *post*, and *topic* info, you should be ok.
- Images are not preserved.  It would be possible to add this feature, but I was working with a forum that blocked almost everything except text, so it was not a priority to me.
- Any non-public information is lost.  Private messages, user profile settings, and a myriad of other things cannot be accessed.

Basically, these scripts may be able to help you save part of an existing forum, but they will require modification for specific tasks and a lot of data will still be lost without the original database.

### A Couple Things to Keep in Mind

Not really caveats, but some things to know:

- By default, `Mongo.py` appends "\_bot" to the end of every username.  I initially liked this idea as a way to differentiate users on the updated system and those merely copied over from the archive.  However, I'm no longer sure about the need for this distinction.  Minor changes to `Mongo.py` can remove this if you would rather not have "\_bot" added to old usernames.
- The users all have blank passwords by default.  This means they cannot be logged into at all because NodeBB does not allow login attempts with blank passwords.  If someone wants to add a feature for creating automatically-generated temp passwords that are hashed and stored into the user profiles, let me know!  Otherwise, there's a couple ways to handle bringing back existing users, which will probably be discussed at the very end.
- Regarding the next section, which comprises the bulk of this README, I'll be focusing on using the scripts in this repo.  Some NodeBB or MongoDB issues could come up, but a number of useful references can be found for those.  As long as you're comfortable with command line, or even just Python, I'm hoping it is pretty straightforward.

## Step-by-Step Usage

The scripts operate on the data in phases, but there's a couple steps to do first.

### Preliminaries - NodeBB and Mongo Installation

#### Step 1: Setup NodeBB with a Mongo backend as [described in the docs](https://docs.nodebb.org/configuring/databases/mongo/)

Some tutorials will install redis, which was the old default, but you'll need Mongo in the last phase.  Anyways, Mongo scales better, is easier to administer, and has better snapshotting.

#### Step 2: In NodeBB's Admin Control Panel, create new Categories for your forum

In myBB or phpBB, subforums typically have a forum ID, but NodeBB has category IDs.  You'll need these category IDs for the first phase.  If you can't find the ID, visit the newly-created category in your browser and check the address bar; "cid=#" should be there somewhere.

#### Optional: Create a Mongo backup to be able to restore

While not strictly necessary, you can potentially save a lot of frustration and lost work by backing up Mongo at each step.

> Backing up Mongo is easy.  To backup the whole system:
> 
> ```
> mongodump -u <admin user> -p "<admin pass>"
> ```
> 
> You can restore the whole system easily, or use the `--db` flag to restore (or backup) certain parts, for instance if you had more than NodeBB running in Mongo.  I use a command like this:
> 
> ```
> mongorestore --db <database name> --drop -u <admin user> --authenticationDatabase "<permission database (typically 'admin')>" --verbose <path to database file dump>
> ```
> 
> Be careful with the `--drop` flag since it will replace everything in the existing database.  This is often what you want but not always.

#### Optional: Install a MongoDB viewer to visually explore and edit data

You can do everything through Python and the Mongo command line, but I prefer having a browser on hand.  I use [Robo 3T](https://robomongo.org) on the Mac, but there's a bunch of options out there.

### Phase 1 - HTML Parsing

The scripts in this phase do most of the heavy lifting.  I started with a single script doing everything, but early on I decided it was unfair to repeatedly ping the server to re-download files.  Plus, some servers may blacklist an IP for doing too much of that.

The result is a separate `Mongo.py` script that handles creating the future MongoDB objects, compatible with NodeBB's schema, and the `html_to_files.py` and `files_to_fields.py` scripts for managing HTML crawling/parsing.

#### Step 3: Run `html_to_files`

This step crawls the existing web server and saves all the forum's topics as local HTML files.

I've included my starting URL, Ambrosia Software's web board for the classic Mac RPG Cythera, but you'll need to edit the script to start at the URL of your desired forum.  Try to use your forum's first page of its topic directory, with settings to view all topics, as the seed.  Also, provide a forum number to the `forum` variable which is used to keep downloaded files organized.

Once the edits have been made, use `python html_to_files.py` to run.  Python will begin saving HTML files in the "data" directory and track links to visit in the "crawl.txt" file.  If your server connection times out or is dropped in this phase, you can restart from where you left off by uncommenting the lines that read in from "crawl.txt".  Make sure to remove the seed URL in this case, or you'll begin a loop of visiting the same links again.

Finally, note that you'll need to re-run the script for each subforum you plan to save.  Because the forum number is used to organize files when writing to disk, you should update it for each forum.

#### Step 4: Run `files_to_fields`

The core script, `files_to_fields.py` parses the saved HTML files and calls `Mongo.py` to build NodeBB-ready objects.  The key fields to track are *users*, *posts*, and *topics*.  Just about every forum system will work if you add the logic to parse out those items.  Check the calls to the `Mongo` object to see what specific data is used.

Before running, you'll need to copy over the seed URLs and forum numbers you used with `html_to_files.py`.[^2]  Unlike that script, which required you to run it separately for each forum, you should put all URLs and forum numbers into `files_to_fields.py`.  Processing everything together is essential if you plan to host them all on the same NodeBB server.

> If subforums are not processed together, user names, posts, and topic IDs all carry a risk of conflicting when attempting to merge the data into a single NodeBB instance.

Next, add the new category numbers you got from **Step 2**.  *You may need to change logic here*.  Starting on line 90, there's a single if-else statement to assign the destination category ID based on the old forum number.  It will need to be extended with additional cases to support more than one or two forums at a time.

*The reply-to handling starting with snapback detection at line 269 will also need changing for different forum URLs.*

With all these changes in place, run `python files_to_fields.py`.  It could take some time, and it will likely need a lot of memory for large amounts of data.  Upon completion, the data will be compressed down into "output.pkl".

A few last things to note:

- Because we are reading from HTML sources and NodeBB uses Markdown for post content, all of the HTML tags need to be stripped out of posts.  I use the external library `html2text` for this task.  It can be installed via pip or swapped with a different HTML -> Markdown converter if you'd like.  I've been happy with this one, although it does sometimes mess with plain-text smilies.
- NodeBB doesn't support smilies, relying instead on unicode emojis.  Most forum systems use a self-hosted set of emoticon images.  To avoid backlinks to the old forum, emoticon images are found and replaced with simple ASCII versions (I didn't want to deal with finding the right emojis!).  The mapping is at the top.
- A couple other features like polls and topic subtitles don't exist in NodeBB, despite being present in most other forum systems.  There's a little extra logic to find these elements and copy them into the top of the NodeBB post.  That at least saves the content.
- This script also uses "crawl.txt" to track its progress but only to load files.  It shouldn't be needed since the risk of server timeouts has been removed.
- The file "links.txt" is used to track links that may need to potentially be fixed.  It is used in the next step, so don't delete it.
- The file "stats.txt", in addition to terminal output, helps log activity, but crucially, it prints out the final user, post, and topic IDs.  **Don't delete "stats.txt" since you'll need these numbers later!**

### Phase 2 - Cleaning Data

By the end of Phase 1, all of the previous forums' data will be extracted, converted, and saved into "output.pkl".  This small phase prepares the data for insertion into the database by trying to remove lingering backlinks and deal with potential Python version differences.

#### Step 5: Run `clean_fields`

Use `python clean_fields.py` for this step; **you should at least edit the template "lookfor" URL on line 24** to be an appropriate link indicator for the host and forum software being targeted.

This script reads in all the data from "output.pkl" and the links that couldn't be resolved from "links.txt".  A number of links couldn't be processed at the time of parsing simply because their corresponding post hadn't been visited yet.  Now that all the posts and topics have been processed, `clean_fields.py` can replace as many links as possible using the internal mapping between old and new post IDs.

There is also code to lock all the topics (in keeping with the "archive" goal of "living archive").  I figured it's easier to unlock recent topics in NodeBB, but I have commented this out by default since it doesn't make sense for most uses.

When finished, the updated data is saved in "output\_final.pkl".

#### Optional: Run `make_compatible` for Python 2 Servers

While I used Python 3 in all the previous steps, I discovered the dependencies didn't all work in Python 3 on the NodeBB server.  I added this step to convert the Python object from Python 3 into a Python 2 compatible list structure.

I don't think an issue will arise if everything is done in Python 2, and there shouldn't be a problem if everything is in Python 3.  In a case like mine, where the server is running a different version, I recommend doing this step.

`python make_compatible.py` simply reads "output\_final.pkl" and writes "output\_compatible.pkl".  I did find the Python 2 Pickle to be slightly more storage efficient.

### Phase 3 - Loading the Database

#### Optional: Copy the data to the server

If your NodeBB instance is hosted elsewhere, you should copy the last Python Pickle, whether the "final" or "compatible" variant over to your server.

> **Turn off NodeBB before each of the following step** and wait to turn it on until at least each step is complete.  Each step deals directly with NodeBB's database and could cause data corruption or loss if NodeBB is left running.

#### Step 6: Run `fields_to_db`

The top of this script needs editing to your MongoDB administrator's username and password.  Also, the current address is appropriate if you are running the script on the server, but you can change it to a different address if desired.  Note that you will need to add permissions in the Mongo authentication database to allow connections from a different host.  Also, you may need to adjust the Pickle file name if you didn't do the compatibility step.

After running `python fields_to_db.py`, you should be able to turn on NodeBB.  If the forum is loading correctly, you're almost done!  If not, better to restore from backup as described above and repeat the last step or two.  Most of the time, if something has gone wrong, there will be some terminal output or error logging to help identify the issue.

#### Step 7: Update the Global Object's ID counters

A critical step that I've not programmed is updating NodeBB's global counters.  I just updated them manually at the end.  It shouldn't be difficult to add this feature into the `fields_to_db.py` script, but I haven't bothered.

Open "stats.txt" from **Step 4**.  At the very bottom, it should report the overall number of users, topics, and posts.

You need to edit the entry in the "objects" collection of NodeBB's database which has the _key "global".  Inside that object are values for "nextUid", "nextTid", and "nextPid".  Replace them with the numbers obtained from the bottom of "stats.txt", **with a small buffer added** (i.e. 10 or 20 higher to protect against overwriting).

You can also replace the "userCount", "topicCount", and "postCount" numbers.  The overall stats will work here, but the more accurate numbers would be the summation of the individual category counts printed in "stats.txt".  There is a small buffer defined at the top of `Mongo.py` to avoid overwriting existing users that could throw off the count.  More specifically, the uid is initialized at 5 instead of 1 because NodeBB will already have at least an administrator user even for an empty installation.

> While you can make these edits in Mongo's command line, I used Robo 3T to easily locate and change the global object.  Make a connection to your MongoDB in Robo 3T, locate NodeBB's database from the sidebar, and open the "objects" collection.  You can use this search to show the global object:
> 
> ```
> db.getCollection('objects').find({'_key':'global'})
> ```

**If you don't do this step, new topics and posts will quickly start overwriting the old ones**, wreaking havoc with the system.  After this is complete, you should have a functioning, "live archive" of the original forum you were aiming to save.

#### Optional: Update Category counts

Similar to the last step, you can use the numbers printed in "stats.txt" to update individual category counts.

The following Mongo command will allow you to locate category objects:

```
db.getCollection('objects').find({'_key':{$regex: "category:"}})
```

From there, update each catgory's "post_count" and "topic_count".  If you have parent categories, leave their values unchanged; NodeBB automatically sums counts of children categories.  These numbers track only posts and topics within the current category.

#### Optional: Add Searching

NodeBB supports very good, fast searching.  In the Admin CP, you can enable the DB Search plugin.  This will add two collections: `searchpost` and `searchtopic`.  They're basically just the text from all topics and posts stored in a manner that MongoDB can quickly parse.

Once the search plugin is enabled, you can turn off NodeBB, and run `python fields_to_search.py` to populate the search collections with the new data.  Forum-wide search should now work after you start NodeBB again (there may be some indexing time).

#### Optional, possibly unnecessary: Fix User Searching

In the original version, I discovered a bug with the `userslug` field a little too late to fix until everything was in the database.  I honestly can't recall if it's been fixed in the current `Mongo.py` version or not.

If you're noticing user search is not performing correctly, you probably have the same problem.  Run `python fix_user_search.py` to fix it.  This is a harmless script, so it won't damage a working setup, but it can patch user search to work if it isn't.

### Handling Users

When you get a working setup, you'll likely want a means of bringing back former users.  As I mentioned above, the passwords are all blank by default, so they are all unusable initially.  I envisioned a couple methods:

1. Have users create new accounts and use those going forward, leaving the "\_bot" version intact.  That was partly the motivation for having "\_bot" appended to names, since it leaves original usernames available.  I've become less interested in this strategy as part of the purpose of the "living archive" mantra is that users will continue to be active with their original names.
2. Have users take over the "\_bot" accounts by one of two methods: a) temp passwords or b) merged accounts.  I now favor this option.

For 2a), I created a test user in which I could repeatedly change the password and use them as temp passwords for "\_bot" accounts.  For 2b), you can have users create their own new user and then use that password for their "\_bot" account.  In that case, it's better if users minimize posting with the new account to make merging to their "\_bot" account easier.

Whether you are using a test user to generate temp passwords or users make their own account, you can go into the database and copy the "password" field into the "\_bot" account.  The passwords are stored as hashed characters, so even the administrator will never know them.  The main reason for doing it this way is that NodeBB will produce the hashed password itself, whereas generating your own hash could cause problems if NodeBB applies any extra processing.

> A quick Mongo query to find NodeBB users is:
> 
> ```
> db.getCollection('objects').find({'username':'<name to find>'})
> ```

After a restart, NodeBB should allow the user to login to the "\_bot" account with the password.  From there, the name can be changed, password updated, and other settings adjusted as desired.  In 2b), I experimented with merging accounts manually and had some success, but it is difficult to do in the database, and NodeBB provides no control for it.  It's easier to delete the new account once the "\_bot" account has been claimed.

## In Closing

I'm hoping these scripts and the provided instructions are useful.  I know this document is long, and unfortunately, a lot of editing may be needed for any variation of the task.  Given more time or interest, it might be worth cleaning up the code to function like ready-made tools, but I'm not sure how to even begin handling all the different types of forum software.

For now, I wanted to get this code out there, even if it's still a little unfinished.  In the absence of anything available to automatically generate NodeBB databases from existing data, it's at least something!

---

[^1]: The `Mongo` class is a bit of a misnomer.  It really should be something like `NodeBB` because it manages the NodeBB schema.  I called it Mongo because it is organized into documents for insertion into a Mongo database, and at first, I planned to do the insertion directly in that class.  That was split out as more processing steps were introduced.

[^2]: While it could be done more elegantly, `files_to_fields.py` still uses the original URL to determine the saved HTML file's location in the "data" subdirectory.  This is an unfortunate side effect of the two scripts being derived from the same source, and I didn't write additional logic to parse downloaded files more cleanly.
