#!/usr/bin/env python
import base64
import os
import shutil
import github
from subprocess import call

#Config values
github_login = "vaibhavbansal"
github_password = "Pass123!"
heat_github_user = "heat-ci"
heat_github_template_repo = "heat-templates"
fusion_github_org = "heat-templates"

github_client = github.Github(login_or_token=github_login,
                              password=github_password,
                              base_url="https://api.github.com",
                              user_agent="custom_script")

heat_user = github_client.get_user(heat_github_user)
fusion_org = github_client.get_organization(fusion_github_org)
repo = heat_user.get_repo(heat_github_template_repo)
print "Getting file list of prod folder"
files = repo.get_dir_contents("prod", "master")

shutil.rmtree('fusion-templates', ignore_errors=True)
os.makedirs('fusion-templates')
print "Created fusion-templates folder"
os.chdir('fusion-templates')

for file in files:
    repo_name = file.name.replace('.template', '')
    try:
        repo = fusion_org.create_repo(repo_name, auto_init=True)
        print "Created %s repo" % repo_name
    except github.GithubException as ex:
        if ex.status == 422:
            repo = fusion_org.get_repo(repo_name)
            print "Repository %s already exists" % repo_name
    call(['git', 'clone', repo.clone_url])
    with open("%s/heat.template" % repo_name, 'w') as file_handler:
        file_handler.write(base64.b64decode(file.content))
    print "Created heat.template file in repo %s" % repo_name
    os.chdir(repo_name)
    call(['git', 'add', 'heat.template'])
    call(['git', 'commit', '-m', '"Added template file"'])
    call(['git', 'push', 'origin', 'master'])
    print "Pushed heat.template file for repo %s" % repo_name
    os.chdir('../')
os.chdir('../')
shutil.rmtree('fusion-templates', ignore_errors=True)
