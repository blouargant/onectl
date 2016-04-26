#!/usr/bin/python -u
''' Predefined regexp epressions '''

IFNAME = '^([0-9A-Za-z]*)([-_]{,1})([0-9A-Za-z]*)([0-9]{1,})$'
VLAN = '^([1-3]?[0-9]{1,3}|40[0-8][0-9]|409[0-5])$'
HOSTNAME = "(?:(?:(?:(?:[a-zA-Z0-9][-a-zA-Z0-9]{0,61})?[a-zA-Z0-9])[.])*(?:[a-zA-Z][-a-zA-Z0-9]{0,61}[a-zA-Z0-9]|[a-zA-Z])[.]?)"
PASSWORD = "^[a-zA-Z0-9_-]{3,20}$"


