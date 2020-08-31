##Modify this file or create a file called local_settings.py

## Location to save images and post data from Instagram
folder = '~/Instagram'

##Instagram Account to download omit at-sign
instagram_username = 'shedd_aquarium'

#Mastodon or Pixelfed instance URL to post to, omit trailing slash
instance_url = 'https://pixelfed.social'

## Personal access token for Mastodon/Pixelfed access
## For pixelfed use https://<INSTANCE_URL>/settings/applications
access_token = 'PASTE_ACCESS_TOKEN_HERE'

##Visibility of fediverse posts, must be one of ['direct', 'private', 'unlisted', 'public']
post_visibility = 'public'

##Optional: you can copy the sessionid and ds_user_id from a logged-in browser session
ds_user_id = ''
sessionid = ''