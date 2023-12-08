
def unpack_tagsets(tag_options_list):
	if len(tag_options_list) == 0:
		return []
	curr = list(tag_options_list[0])
	if len(tag_options_list) == 1:
		return [[unpacked] for unpacked in curr]
	
	return [
		[elem] + unpacked
		for elem in curr
		for unpacked in unpack_tagsets(tag_options_list[1:])
	]
