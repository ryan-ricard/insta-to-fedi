import requests
import json
import shelve
import os
import re
from collections import namedtuple
from InstagramPost import InstagramPost

try:
	import local_settings as settings
except ImportError:
    import settings


def _json_object_hook(d): return namedtuple('X', d.keys(), rename=True)(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)


def main():
	with shelve.open(os.path.join(settings.folder, "posts.db"), flag="c") as db:
		download_recent_insta_posts(db)
		upload_new_posts(db)
		


def download_recent_insta_posts(db):
	wrote_something = False

	cookies = {}
	if len(settings.ds_user_id) > 0 and len(settings.sessionid) > 0:
		cookies = dict(
			ds_user_id=settings.ds_user_id,
			sessionid=settings.sessionid
		)


	resp = requests.get('https://www.instagram.com/'
		+settings.instagram_username+
		'/?__a=1',
		cookies=cookies
    )

	if resp.status_code == 200:
		insta_data = json2obj(resp.text)
		posts = insta_data.graphql.user.edge_owner_to_timeline_media.edges
		for p in posts:
			if p.node.id not in db:
				post = InstagramPost()
				post.id = p.node.id
				post.shortcode = p.node.shortcode
				post.instagram_url = p.node.display_url
				post.height = p.node.dimensions.height
				post.width = p.node.dimensions.width
				post.is_video = True if "true" else False
				post.accessibility_caption = p.node.accessibility_caption
				cap_list = p.node.edge_media_to_caption.edges
				if len(cap_list) > 0:
					post.photo_caption = cap_list[0].node.text

				print("Downloading post id " + post.id)
				img_file = post.id +".jpg"
				if post.instagram_url.find('/'):
					img_file = post.instagram_url.rsplit('/', 1)[1]
					img_file = img_file[0:img_file.index("?")]
				img_path = os.path.join(settings.folder, img_file)
				img_resp = requests.get(post.instagram_url, allow_redirects=True)
				open(img_path, 'wb').write(img_resp.content)
				wrote_something = True
				post.local_path = img_path
				db[post.id] = post
		if not wrote_something:
			print("No new posts to download from Instagram")
	else:
		print("Error downloading instagram posts")

def upload_new_posts(db):
	uploaded_something = False
	for key in db:
		post = db[key]
		if post.fediverse_url == "":
			new_url = post_to_fediverse(post)
			if new_url and len(new_url) > 0:
				uploaded_something = True
				post.fediverse_url = new_url
				db[key] = post
	if not uploaded_something:
		print("No new posts to upload to fediverse")

def find_cw(caption):
	is_cw = 'false'
	cw_text = ""
	#Look for the exact hashtag #CW or #cw
	if re.search(r"#[cC][wW]\b", caption):
		is_cw = 'true'
	##Look for a hashtag like #CW_Food
	match = re.search(r"#[cC][wW]_([\w]+)\b", caption)
	if match:
		is_cw = 'true'
		cw_text = match.group(1)

	return is_cw, cw_text

def post_to_fediverse(post_data):
	print("Uploading post " + post_data.id)
	filename = post_data.local_path
	is_cw, cw_text = find_cw(post_data.photo_caption)
	url = settings.instance_url + '/api/v1/media'
	headers = {'Authorization': 'Bearer '+ settings.access_token}
	files = {'file': open(os.path.join(settings.folder, filename),'rb')}
	formData = {'description': post_data.accessibility_caption}
	resp = requests.post(url, files=files, data=formData, headers=headers)
	if resp.status_code == 200:
		media_data = json2obj(resp.text)
		media_id = media_data.id
		status_url = settings.instance_url + '/api/v1/statuses'
		formData = {
			'status': post_data.photo_caption, 
			#This works fine for one image, but I'd probably want to send JSON for >1
			'media_ids[]': [media_id], 
			'visibility':settings.post_visibility,
			'sensitive': is_cw,
			'spoiler_text' : cw_text
		}
		resp = requests.post(status_url, data=formData, headers=headers)
		post_data = json2obj(resp.text)
		if len(post_data.url) > 0:
			return post_data.url
		else:
			return None

if __name__ == "__main__":
    main()


