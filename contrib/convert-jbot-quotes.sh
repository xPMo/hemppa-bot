#!/bin/sh
jq '
	. | with_entries( .key |= ascii_downcase) | {
		"quotes": with_entries( .value |= .":quotes" ),
		"aliases": to_entries | map( {(.value.":aliases"[]? | ascii_downcase): .key} ) | add
	}
'
