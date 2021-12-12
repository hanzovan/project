# Project title: ITEMS PLANNER
#### Video Demo: <URL HERE>
#### Description:

#### Items Planner is simply a web application that help users to store their physical items information,
then suggest users on how much money they should deposit into their saving account each month. When the item need maintenance or replacement, users would be
well-prepared with their savings.

#### The users were allowed to store informations including Item's name, Price, Bought Date, estimated Lifetime, maintenance cost per month, Warranty,
Brand, Seller. Based on input data, the app will calculate other variables of item such as Used time, Recommended replace date, depreciation cost per month,
remained book value, savings user should have to the current time for this item's replacement. All details will be shown in the item page.

#### In the index page, the app will show general information of the user containing number of items owned by user,
total cost per month for all items he or she has, total savings the user should have in current time. In addition,
index page also shows number of items need to be replace within 30 days.

#### When users replace an item, they were allowed to note the price they sold their items to other people as well as the reason they need to replace it.
The item will be removed from item list and store in history page, which will be no longer affect user's cost anymore.
The users can access removed item in history at any time though.

#### In case users did not buy the item but will do it in the future, Items Planner allow users to add the items to their wishlist,
which will help them to consider the cost per month before actually buying it. When buying from wishlist, the information will be directly move from wishlist to the item list.

Items Planner project was designed using Python, Flask, SQLite. In my project folder, there are 3 directories which include flask_session, static, and templates.
flask_session was automatically created by Flask
static contains my css, video, and photo for the web application.
templates made up of 17 templates which will work with application.py to run the whole process

assets.db is a SQLite file used to store user's information using 4 tables: users, items, history, wishlist

	users table has 9 columns:
		id: this is the user id which will be stored in session
		username: this is the name choose by user, which need to be unique for every user and shown on the navigation bar
		hash: for security, the app store only hash of the user's password, not the actual password itself
		item quantity: this is the total number of user's items
		total_depr: sum of all items' depreciation per month owned by that user
		all_items_maint: sum of all items' maintenant cost per month owned by the user
		monthly_total: sum of total_depr and all_items_maint, which is the money that user should save that month for all the monthly cost in this app
		total_savings: sum of all savings the user should have to the current time
		items_repl: number of items need to be replace in 30 days as well as items were not replaced in time

	items table has 14 columns, including:
		id: item's unique id. However, I won't be sure if 2 users commit add items at the same time, which will create the same id for 2 items for 2 different users.
			Therefore, everytime updating a record, the app uses 2 different condition: item's id and user's id, which will solve the issue.
			I will look into this and solve the issue more efficiently.
		user_id: user's id, which used to allow querying items for each user.
		item: item's name, which do not need to be unique
		price: item's price
		bought: the date the user bought the item
		used: the number of month the item was used, calculated from the bought date to current date
		should_replace: the date the item should be replaced due to the used time and the lifetime which was estimated by user from the beginning.
		depreciation_per_month:  the monthly depreciation cost of item, which was calculated by the original price, divided by the lifetime chose by user.
		book_value: the value of item after subtract the depreciation cost from the original price, when the item's lifetime come to it's limit,
				the book_value will be at 0.
		savings_should_have: the savings the user should currently have for this particular item
		brand: the brand of the item
		seller: the shop or seller that user bought item from
		warranty: the date the warranty expire
		maint: the maintenant cost per month of the item

	history has similarly information as items, but reduced to 12 columns:
		id: item's id
		user_id
		item: item's name
		price
		book_value
		sold_price: which shown the price the user sold the item to regain some profit
		profit: by subtracting book_value from sold_price
		bought: the date the item was bought by user
		sold: the date the item was being sold or replaced
		brand
		seller
		reason_replace: left for user to note whether the item was broken after or before lifetime limit, or still working but being replace due to finish depreciation.

	wishlist has similarly information as items, but only show 10 column:
		id of item
		user_id
		item's name
		price
		lifetime
		brand
		seller
		maintenant cost
		depreciation per month
		monthly cost (sum of maintenant cost and depreciation cost per month): this variable is for user to consider whether to buy it now or waiting for
			his income to raise a little bit.

helpers.py is a python app that help to define function using in application.py, including login_required, days_between, and show usd value when needed.

application.py is the python program that used to control the whole system, these are the route I use to implement my web application:

	index(): show the homepage if user did not logged in, or show the user's items information if user did logged in
		this route uses 2 templates file: index.html, index2.html
	login(): allow user to login, using login.html
	register(): allow user to register for new account, using register.html
	logout(): allow user to log out and being redirect to homepage.
	change_pass(): allow user to change their password, using change_pass.html
	add_item(): allow user to add items to their list, using add_item.html and being redirect to items.html
	pre_replace(): let user enter replace page before actually replace their item, using replace.html
	replace_item(): remove the item from item list and move it to history
	history(): Allow user to see information of items they replaced before, using: history.html
	items(): Update all information until current day and show items detail to user, using: items.html
	items_repl(): This hidden page only show when user has items needed to be replaced in 30 days,
			which is like items(), but only show items needed to be replace in 30 days, using: items_repl.html
	delete(): Let user delete item's information in items list
	delete_history(): Let user delete item's information in history
	pre_edit(): Let user enter edit page of their item, using edit.html
	edit(): Let user actually commit the change to the items list
	add_wishlist(): Let user add item to wishlist, using wishlist.html and add_wishlist.html
	wishlist(): Let user see their item in wishlist, using wishlist.html
	delete_wishlist(): Let user delete their item in wishlist
	pre_edit_wishlist(): Let user enter edit page of their item in wishlist using edit_wishlist.html
	edit_wishlist(): Let user commit their edit to the wishlist data
	pre_add_item_from_wishlist(): allow user to enter page in order to add their item from wishlist to item list,
			using add_item_from_wishlist.html.
	add_item_from_wishlist(): allow user to commit action move the item's information from wishlist to item list


