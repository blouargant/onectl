## ONECTL Bash completion
# For alias plugin : is used in the name escape this special character and return it back at the end

USER=$(whoami)

export COMP_WORDBREAKS=${COMP_WORDBREAKS/\:/}
GLOBAL_OPTS="--help --list --dump --load --nolive --show --info --bind --unbind --history --rollback"
SPTH='/usr/share/onectl/plugins/'
check_plugin() {
	rel_path=$(echo $plugin | sed -e "s/\./\//g")
	plug_path="$SPTH$rel_path.py"
	noactions=""
	if [ -e "$plug_path" ]; then
		# Check if it is a symlink to a template
		if [ -L "$plug_path" ]; then
			destination="$(readlink -f $plug_path)"
			xml_path="/usr/share/onectl/plugins/$rel_path.xml"
			# if there is an xml, then take the commands from the xml
			if [ -L "$xml_path" ]; then
				# get the xml type
				file_type=$(sed -n '/<\/file_type>/ {
									s/^.*<file_type>//
									s/<\/file_type>.*$//
									p
									}' $xml_path)
				if [ "ini" == "$file_type" ]; then
					# take the plugin info
					plugin_info=$(sed -n '/'"<name>$plugin"'/,/<\/plugin>/ {
							s/^.*<plugin>//
							s/<\/plugin>.*$//
							p
							}' $xml_path)
					tag="type"
					# get the type value. If a list add add and remove commands
					type_value=$(echo $plugin_info | sed -n '/.*<'"$tag"'>/,/<\/'"$tag"'>/ {
							s/^.*<'"$tag"'>//
							s/<\/'"$tag"'>.*$//
							p
							}' )
					if [ "LIST" == "$type_value" -o "INTEGER-LIST" == "$type_value" ]; then
						choice="--help --info --view  --set --add --remove --disable"
					else
						choice="--help --info --view  --set --disable"
					fi
				else
					actions=$(grep "### OPTION:" $plug_path | sed -e "s/ *$//" | grep -v "info$\|list$\|show$" | sed -e "s/.*OPTION: */--/" | sed -e "s/ *//")
					noactions=$(grep "### NO OPTION:" $plug_path | sed -e "s/ *$//" | grep -v "info$\|list$\|show$" | sed -e "s/.*OPTION: */--/" | sed -e "s/ *//")
					choice="--help --info --view  --set $actions"
				fi
			
			else
				actions=$(get_actions)
				noactions=$(grep "### NO OPTION:" $plug_path | sed -e "s/ *$//" | grep -v "info$\|list$\|show$" | sed -e "s/.*OPTION: */--/" | sed -e "s/ *//")
				choice="--help --info --view  --set $actions"
			fi
		else
			actions=$(get_actions)
			noactions=$(grep "### NO OPTION:" $plug_path | sed -e "s/ *$//" | grep -v "info$\|list$\|show$" | sed -e "s/.*OPTION: */--/" | sed -e "s/ *//")
			choice="--help --info --view  --set $actions"
		fi
	else
		choice=""
	fi
	for toremove in $noactions; do
		tmp=$choice
		choice=$(echo $tmp | sed -e "s/$toremove *//")
	done
}

get_actions() {
	actions=$(grep "### OPTION:" $plug_path | sed -e "s/ *$//" | grep -v "info$\|list$\|show$" | sed -e "s/.*OPTION: */--/" | sed -e "s/ .*//" | sed -e "s/\[[[:alnum:]]*\]//g")
	echo "$actions"
}

get_extended_actions() {
	CHECK_OPT=$1
	plg_opt_path=""
	multi_choice=""
	ACTS=$(grep "### OPTION:" $plug_path | sed -e "s/ *$//" | grep -v "info$\|list$\|show$" | sed -e "s/.*OPTION: */--/" | sed -e "s/ \[/_[/")
	for action in "$ACTS"; do
		if [ $(echo "$action" | sed -e "s/_.*//" | grep -e "^$CHECK_OPT$") ]; then
			TEST_PATH=$(echo "$action" | grep "_\[PATH\]")
			TEST_MULTI=$(echo "$action" | grep "_\[.*\]")
			if [ "$TEST_PATH" ]; then
				shorted=$(echo $action | sed -e "s/_.*//")
				plg_opt_path="$plg_opt_path $shorted"
			elif [ "$TEST_MULTI" ]; then
				multi_choice=$(echo $action | sed -e "s/.*_\[//" | sed -e "s/\].*//")
			fi
		fi
	done
}

check_option_old() {
	first_dash=$(echo $OPT_WORD | grep "^-")
	if [ "$first_dash" ]; then
		choice=$GLOBAL_OPTS
	elif [ "$OPT_WORD" == "--load" ]; then
		get_path
	else
		choice=$(find "$SPTH" | grep "\.py$" | grep -v "~$" | sed -e "s/.*plugins.//" | sed -e "s/.py$//" | sed -e "s/\//./g")
	fi
}

check_option() {
	first_dash=$(echo $OPT_WORD | grep "^-")
	if [ "$first_dash" ]; then
		choice=$GLOBAL_OPTS
	elif [ "$OPT_WORD" == "--load" ]; then
		get_path
	else
		get_plugin_list
	fi
}
get_plugin_list_old() {
	TMPWORD=$(echo $OPT_WORD | sed -e "s|\.|/|g" |sed -e "s|/$||")
	DIR_LST=$(find "$SPTH" | grep "\.py$" | grep "plugins\/$TMPWORD" | grep -v "~$" | sed -e "s/.*plugins.//" | sed -e "s/.py$//")
	if [ "$TMPWORD" ]; then
		choice=$(echo -e "$DIR_LST" | sed -e "s|\($TMPWORD/\([A-Za-z0-9]*-*_*[A-Za-z0-9]*:*[0-9]*\)*\)/.*|\1/|g" | sed -e "s|/|.|g")
	else
		choice=$(echo -e "$DIR_LST" | sed -e "s|\(\([A-Za-z0-9]*-*_*[A-Za-z0-9]*:*[0-9]*\)*\)/.*|\1/|g" | sed -e "s|/|.|g")
	fi
}

get_plugin_list() {
	TMPWORD=$(echo $OPT_WORD | sed -e "s|\.|/|g" |sed -e "s|/$||" | sed -e "s| $||")
	FULL_PATH="$SPTH$TMPWORD"
	while [ ! -d $FULL_PATH ]; do
		NEW_PATH=${FULL_PATH%\/*}
		FULL_PATH=$NEW_PATH
	done
	
	TEST_WORD="$SPTH$TMPWORD"
	KEY_LIST=$(find $FULL_PATH/ | grep "$TEST_WORD" | grep "\.py$" | grep -v "~$" | sed -e "s/.py$//")
	CONTENT_LIST=""
	TMP_PLG_PATH=${FULL_PATH##*"/usr/share/onectl/plugins"}
	PLG_PATH=$(echo "$TMP_PLG_PATH" | sed -e "s|^/||")
	for KEY in $KEY_LIST; do
		TMP_KEY=${KEY##*$FULL_PATH/}
		NEW_KEY=${TMP_KEY%%\/*}
		if [ ! "$NEW_KEY" ]; then
			NEW_KEY="$TMP_KEY"
		elif [ -d "$FULL_PATH/$NEW_KEY" ]; then
			NEW_KEY="$NEW_KEY/"
		fi
		if [ "$PLG_PATH" ]; then
			TEST=$(echo -e "$CONTENT_LIST" | grep " $PLG_PATH/$NEW_KEY ")
			if [ ! "$TEST" ]; then
				CONTENT_LIST="$CONTENT_LIST $PLG_PATH/$NEW_KEY "
			fi
		else
			# We are at root plugins
			TEST=$(echo -e "$CONTENT_LIST" | grep " $NEW_KEY ")
			if [ ! "$TEST" ]; then
				CONTENT_LIST="$CONTENT_LIST $NEW_KEY "
			fi
		fi
	done
	choice=$(echo -e "$CONTENT_LIST" | sed -e "s|/|.|g" | sed -e "s/^ //" | sed -e "s/ $//")
	if [ $(echo "$choice" | wc -w) -eq 1 ]; then
		if [ $(echo "$choice" | grep "\.$") ]; then
			# We extend the list if there is only one subdir available
			OPT_WORD=$choice
			get_plugin_list
		fi
	fi
		
	echo "#$choice#" >> /tmp/onectl-$USER.tmp
}

get_path()
{
	if [ ! "$OPT_WORD" ]; then
		choice=$(ls)
	else
		FULL_PATH=$OPT_WORD
		LOCAL_FILE=$(echo $FULL_PATH | grep "^[A-Za-z]")
		if [ "$LOCAL_FILE" ]; then
			TMP_PATH="$PWD/$FULL_PATH"
			FULL_PATH=$TMP_PATH
			TMP_WORD="$PWD/$OPT_WORD"
			OPT_WORD=$TMP_WORD
		fi
		while [ ! -d $FULL_PATH ]; do
			NEW_PATH=${FULL_PATH%\/*}
			FULL_PATH=$NEW_PATH
		done
		if [ ! "$FULL_PATH" ]; then
			FULL_PATH="/"
		fi
		CONTENT_LIST=$(find $FULL_PATH -maxdepth 1 | grep "^$OPT_WORD")
		if [ "$LOCAL_FILE" ]; then
			choice=$(echo -e "$CONTENT_LIST" | sed -e "s|^$PWD/||" | sed -e "s/ $//" | sed -e "s/^ //")
		else
			choice=$(echo -e "$CONTENT_LIST" | sed -e "s/^ //" | sed -e "s/ $//")
		fi
		if [ $(echo "$choice" | wc -w) -eq 1 ]; then
			if [ -d "$choice" ]; then
				# We extend the list if there is only one subdir available
				OPT_WORD="$choice/"
				get_path
			fi
		fi
	fi
}
_onectl() {
	local choice current plg_opt_path
	MULTI_OPTS="-n -d --nolive --show --info"
	SHOW_OPTS="--show --info --dump --list"
	case "$COMP_CWORD" in
		# If we are at the first parameter, then list all available plugins
		1)
			OPT_WORD=${COMP_WORDS[1]}
			check_option
			choice="$choice"" [--OPT]"
			;;
		
		# On the second level, list possible actions
		2)
			first_opt=$(echo ${COMP_WORDS[1]} | grep "^-")
			if [[ $MULTI_OPTS =~ (^| )${COMP_WORDS[1]}($| ) ]]; then
				OPT_WORD=${COMP_WORDS[2]}
				check_option
			elif [ -z "$first_opt" ]; then
				plugin=${COMP_WORDS[1]}
				check_plugin
			elif [ "${COMP_WORDS[1]}" == "--dump" ]; then
				OPT_WORD=${COMP_WORDS[2]}
				check_option
			elif [ "${COMP_WORDS[1]}" == "--help" ]; then
				choice=''
			elif [ "${COMP_WORDS[1]}" == "--list" ]; then
				OPT_WORD=${COMP_WORDS[2]}
				get_plugin_list
			elif [ "${COMP_WORDS[1]}" == "--bind" -o  "${COMP_WORDS[1]}" == "--unbind" ]; then
				OPT_WORD=${COMP_WORDS[2]}
				get_plugin_list
			elif [ "${COMP_WORDS[1]}" == "--load" ]; then
				OPT_WORD=${COMP_WORDS[2]}
				get_path
			elif [ "${COMP_WORDS[1]}" == "--rollback" ]; then
				choice='ID'
			elif [ "${COMP_WORDS[1]}" == "--history" ]; then
				choice='ID'
			else
				choice=""
			fi
			;;
		3)
			last_opt=$(echo ${COMP_WORDS[2]} | grep "^-")
			if [ "${COMP_WORDS[1]}" == "--load" ]; then
				OPT_WORD=${COMP_WORDS[3]}
				get_path
			elif [ "${COMP_WORDS[1]}" == "--bind" -o "${COMP_WORDS[1]}" == "--unbind" ]; then
				OPT_WORD=${COMP_WORDS[3]}
				get_plugin_list
			elif [[ $SHOW_OPTS =~ (^| )${COMP_WORDS[1]}($| ) ]]; then
				choice=''
			elif [ -z "$last_opt" ]; then
				plugin=${COMP_WORDS[2]}
				check_plugin
			elif [ "${COMP_WORDS[2]}" == "--view" ]; then
				choice='actual saved diff'
			else
				get_extended_actions ${COMP_WORDS[2]}
				if [ "$plg_opt_path" ]; then
					OPT_WORD=${COMP_WORDS[3]}
					get_path
				elif [ "$multi_choice" ]; then
					choice="$multi_choice"
				else
					choice=''
				fi
			fi
			;;
		4)
			last_opt=$(echo ${COMP_WORDS[3]} | grep "^-")
			if [ "${COMP_WORDS[1]}" == "--load" ]; then
				OPT_WORD=${COMP_WORDS[4]}
				get_path
			elif [ "${COMP_WORDS[2]}" == "--load" ]; then
				OPT_WORD=${COMP_WORDS[4]}
				get_path
			elif [ "${COMP_WORDS[3]}" == "--view" ]; then
				choice='actual saved diff'
			else
				EXTENDED=$(get_extended_actions)
				if [ "$( echo $EXTENDED | grep -e "${COMP_WORDS[3]}\( \|$\)" )" ]; then
					OPT_WORD=${COMP_WORDS[4]}
					get_path
				else
					choice=''
				fi
			fi
			;;
		5)
			last_opt=$(echo ${COMP_WORDS[4]} | grep "^-")
			if [ "${COMP_WORDS[1]}" == "--load" ]; then
				OPT_WORD=${COMP_WORDS[5]}
				get_path
			elif [ "${COMP_WORDS[2]}" == "--load" ]; then
				OPT_WORD=${COMP_WORDS[5]}
				get_path
			elif [ -z "$last_opt" ]; then
				plugin=${COMP_WORDS[4]}
			elif [ "${COMP_WORDS[4]}" == "--view" ]; then
				choice='actual saved diff'
			else
				EXTENDED=$(get_extended_actions)
				if [ "$( echo $EXTENDED | grep -e "${COMP_WORDS[4]}\( \|$\)" )" ]; then
					OPT_WORD=${COMP_WORDS[5]}
					get_path
				else
					choice=''
				fi
			fi
			;;
		*)
			words=()
			;;
	esac
	# creat the final list of choices
	current=${COMP_WORDS[COMP_CWORD]}
	COMPREPLY=( $( compgen -W '$choice' -- $current) )
}

complete -F _onectl onectl


