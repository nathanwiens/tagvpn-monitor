import requests, json, time
import meraki, config

api_key = config.api_key
org_id = config.org_id
uplink1 = config.uplink1

#EXCLUDE MONITORING THESE IPS, USUALLY ANY VPN ADDRESSES
ipToExclude  = ['8.8.8.8','8.8.4.4','1.1.1.1','208.67.220.220','208.67.222.222']

while True:
    #previousNetwork = ""
    
    #GET UPLINK LATENCY AND LOSS INFO FOR ALL MONITORED IPS IN ALL NETWORKS
    orgloss = meraki.getorguplinklosslatency(api_key, org_id, uplink1)
    vpn_sites = meraki.getnonmerakivpnpeers(api_key, org_id)
    primary_vpn_ips = []
    backup_vpn_ips = []
    for vpn in vpn_sites:
        for tag in vpn["networkTags"]:
            if "_primary" in tag:
                print("Primary VPN Added : "+vpn["name"])
                primary_vpn_ips.append(vpn["publicIp"])
            elif "_backup" in tag:
                print("Backup VPN Added : "+vpn["name"])
                backup_vpn_ips.append(vpn["publicIp"])
    monitored_net_ids = []
    
    for network in orgloss:
        
        tagsAfter = [] #ARRAY WITH FINAL TAGS
        tagsString = "" #STRING WITH FINAL TAGS
        #ONLY PERFORM ONE ACTION PER NETWORK (IN CASE OF MULTIPLE MONITORED IPS)

        if network['ip'] in primary_vpn_ips or network['ip'] in backup_vpn_ips:
            if network['ip'] in primary_vpn_ips:
                isprimary = 1
            elif network['ip'] in backup_vpn_ips:
                isprimary = 0
            
            skipNetwork = False
            loss=False
            swapped = False
            
            #GET NETWORK INFO
            network_info = meraki.getnetworkdetail(api_key, network['networkId'])
            print("-------------------------------------")
            print("Network Name : "+network_info['name'])
            print("Network Id : "+network['networkId'])
            print("Device Serial : "+network['serial'])
            print("Monitored IP : "+network['ip'])
            print("Primary? ")
            print(isprimary)
            
            networklosslatency = meraki.getuplinklosslatency(api_key, network['networkId'], network['serial'], uplink1, network['ip'], timespan=120)
            
            #GET ALL TAGS IN NETWORK, AND LOOK FOR tcr_primary, tcr_backup, and tcr_swapped
            tagsBefore = network_info['tags'].split(' ')
            for tag in tagsBefore:
                if "tcr_primary" in tag:
                    primary = tag
                    print("Primary TCR : " + primary)
                elif "tcr_backup" in tag:
                    backup = tag
                    print("Backup TCR: " + backup)
                elif tag == "tcr_swapped":
                    swapped = True
                else:
                    tagsAfter.append(tag)
            
            #CHECK CONNECTIVITY HEALTH, IF UNDERPERFORMING OR UPLINK DOWN, SWAP PRIMARY AND BACKUP TAGS, AND ADD tcr_swapped TAG
            if isprimary == 1 or (isprimary == 0 and swapped == True):
                for iteration in networklosslatency:
                    print(iteration)
                    if iteration['lossPercent'] >= 30 or iteration['latencyMs'] >= 100:# or uplink_status is not 'Active':
                        loss=True
                        if isprimary == 0:
                            print("Backup failed. Changing from Backup to Primary")
                            tagsAfter.append(primary.split("_down")[0]+"_up")
                            tagsAfter.append(backup.split("_up")[0]+"_down")
                            for tag in tagsAfter:
                                tagsString+= tag + " "
                            print("New List of Tags : "+tagsString)
                            new_network_info = meraki.updatenetwork(api_key, network['networkId'], tags=tagsAfter)
                            break
                        else:
                            print("Primary failed. Changing from Primary to Backup - "+str(iteration['lossPercent'])+"% - "+str(iteration['latencyMs'])+"ms")
                            tagsAfter.append(primary.split("_up")[0]+"_down")
                            tagsAfter.append(backup.split("_down")[0]+"_up")
                            tagsAfter.append("tcr_swapped")
                            for tag in tagsAfter:
                                tagsString+= tag + " "
                            print("New List of Tags : "+tagsString)
                            new_network_info = meraki.updatenetwork(api_key, network['networkId'], tags=tagsAfter)
                            break
                    else:
                        print("Everything looks good. Carry on.")

    print("Sleeping for 5s...")
    print("#####################################")
    print("#####################################")
    time.sleep(5)