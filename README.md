# Tag-Based IPsec VPN Failover
This script is based almost completely on the one available here, written by Chris Weber: https://documentation.meraki.com/MX/Site-to-site_VPN/Tag-Based_IPSEC_VPN_Failover. You can also find documentation on how to use the tags to map IPSec peers to Networks on the same page

This script tracks latency and loss to an IPSec VPN peer along with status of a WAN link, and swaps Network tags in the event of poor performance/uplink down.

Variables you'll need to set can be found in the config.py file.
You must set the API Key and Organization ID for this script to run.

The basic flow/purpose of this functionality is:
1. Create the following set tags for each pair of VPN peers to use:
   friendlyname_primary_up
   friendlyname_primary_down
   friendlyname_backup_up
   friendlyname_backup_down
   friendlyname_swapped
2. On the MX Network, add the "friendlyname_primary_up" and "friendlyname_backup_down" tags from the Organization > Overview page
3. Configure primary and backup IPSec Peers under Security & SD-WAN > Site-to-site VPN with the same private subnets. For the primary peer, add the "friendlyname_primary_up" tag, and for the backup peer, add "friendlyname_backup_up"
4. Run the script

With this setup, the MX will only match a peer with the "up" tag, so under normal conditions it will match the primary peer but not the backup. In a failover condition, it will no longer match the "primary_up" tag so that peer will be removed, and it will begin to match the "backup_up" tag so it will add that VPN peer. The "friendlyname_swapped" tag is used to track which Networks have failed over, and can be used to filter the Organization > Overview page for easy tracking.
