# Ansible Rulebook + Dynatrace DEMO

## Description
In this demo we will register a host to Dynatrace and set up a webhook to send
problem notifications to ansible-rulebook CLI. Dynatrace monitors the
availability of a process. Upon receiving a problem notification the ansible-
rulebook CLI runs a remedy playbook to restart the process.

## Instructions
### Nodes or instances
* Rulebook Node: The node where the ansible-rulebook CLI is running
* Client Node: The node where the monitored process is running
* Dynatrace Console: An active Dynatrace tenant and its web console

### Set up client node
1. Prepare a VM with host name called `lamp`
2. Install Dynatrace OneAgent. Host `lamp` then should appear in Dynatrace
console
3. Have python3 installed
4. Copy `fake_app.py` under path `/root/fake-app`. Run `python3 fake_app.py`.
`fake_app.py` is a web app with two GET endpoints running on port 5080.
`<lamp ip>:5080/health` will return `{"status": "RUNNING"}`.
`<lamp ip>:5080/down` will force the app to exit, simulating a process
crashing.
5. Make the client node ansible accessible from the rulebook node.

### Set up the rulebook node
1. Have ansible-rulebook CLI and its dependencies installed
2. Have ansible.eda collection installed by ansible-galaxy
3. Update `inventory.yml` with correct ip and user to access the client node
4. Start the rulebook CLI:
```shell
  ansible-rulebook -i demos/dynatrace-demo/inventory.yml --rules demos/dynatrace-demo/rulebook.yml
```
This rulebook starts an alertmanager source that listens on port 5050

### Configure Dynatrace
1. On the console window go to `Settings/Integrations/Problem notifications`.
Add a new notification with type `Custom Integration`. Set the webhook URL to
`<rulebook node ip>:5050/dynatrace`. Make sure the URL is publicly accessible.
Otherwise use a reverse proxy.
2. Go to `Settings/Processes and containers/Process availability`. Add a new
monitoring rule. Add a new detection rule with process property = `Command line`
and Condition = `$suffix(fake_app.py)`. Save the monitored rule name as
`pythonmain`

### Test
1. Use a curl or similar command to request `http://<lamp ip>:5080/health`. It
should response properly
2. Make request `http://<lamp ip>:5080/down` to shutdown the fake_app
3. Wait a few minutes and observe Dynatrace console window. The Problems page
should report a problem
4. The rulebook CLI should respond to the problem and run a playbook
5. Dynatrace should then change the problem status to `Closed`
6. Verify `http://<lamp ip>:5080/health` is responding again
