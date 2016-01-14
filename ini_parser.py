#!/usr/bin/env python
# -*- coding:utf-8 -*-

# description:

import re
import json


class IniParse(object):
    def __init__(self):
        self.content_list = []

    def read(self, file_path):
        with open(file_path, 'r') as fp:
            current_option = None
            for line_no, line in enumerate(fp):
                line = line.strip()
                if re.match('\s*;', line) or re.match('\s*#', line):
                    self.content_list.append({"type": "comment", "value": line, "src_string": line})
                elif re.match('\s*\[.+\]\s*', line):
                    tmp = re.sub("\[", "", line)
                    section_name = re.sub("\]", "", tmp)
                    self.content_list.append({"type": "section", "name": section_name, "src_string": line})
                    current_option = section_name
                elif not re.search("\s*\[", line) and re.match("\s*.+", line):
                    tmp_val = re.sub("\s", "", line)
                    tmp_list = tmp_val.split("=")
                    # print tmp_list
                    value = tmp_list[1]
                    option_name = tmp_list[0]
                    self.content_list.append({"type": "option",
                                              "value": value,
                                              "name": option_name,
                                              "in_section": current_option,
                                              "src_string": line})
                elif re.match("\s*", line):
                    self.content_list.append({"type": "comment", "value": "", "src_string": ""})

    def sections(self):
        return [each["name"] for each in self.content_list if each["type"] == "section"]

    def has_section(self, section_name):
        return section_name in self.sections()

    def options(self, section_name):
        return [each["name"] for each in self.content_list if each["type"] == "option" and each["in_section"] == section_name]

    def has_option(self, section_name, option_name):
        return all([each for each in self.content_list if each["type"] == "option" and each["in_section"] == section_name])

    def get(self, section_name, option_name):
        tmp =  [each["value"] for each in self.content_list if each["type"] == "option" and each["in_section"] == section_name and each["name"] == option_name]
        return tmp[0] if tmp else None

    def set(self, section_name, option_name, new_value):
        for each in self.content_list:
            if each["type"] == "option" and each["in_section"] == section_name and each["name"] == option_name:
                each["value"] = new_value
                each["src_string"] = "{} = {}".format(each["name"], new_value)

    def write(self, file_path):
        ret = ""
        for each in self.content_list:
            ret += "{}\n".format(each["src_string"])
        with open(file_path, "w") as fp:
            fp.write(ret)

def get_dict_value_from_ini(ini_path, ignore_section=False):
    ini_parse_obj = IniParse()
    ini_parse_obj.read(ini_path)
    all_sections = ini_parse_obj.sections()
    ret = {}
    for each_section_name in all_sections:
        all_options_in_section = ini_parse_obj.options(each_section_name)
        if not ignore_section:
            ret[each_section_name] = {}
        for each_option_name in all_options_in_section:
            if ignore_section:
                ret[each_option_name] = ini_parse_obj.get(each_section_name, each_option_name)
            else:
                ret[each_section_name][each_option_name] = ini_parse_obj.get(each_section_name, each_option_name)
    return ret

def set_new_to_ini(ini_path, new_json_content):
    ini_parse_obj = IniParse()
    ini_parse_obj.read(ini_path)
    new_value_dict = json.loads(new_json_content)
    for each_section_name, each_section_option_value in new_value_dict.iteritems():
        for each_option, each_v in each_section_option_value.iteritems():
            ini_parse_obj.set(each_section_name, each_option, each_v)
    ini_parse_obj.write(ini_path)

if __name__ == "__main__":
    import argparse

    parse = argparse.ArgumentParser()
    parse.add_argument("i", help="params means input ini path")
    parse.add_argument("-n", "--new_value", dest="new_value", help="params means new value 2 set in ini file, format is json")
    args = parse.parse_args()
    if args.i and args.new_value:
        set_new_to_ini(args.i, args.new_value)
    else:
        print parse.print_help()