import requests, json, time
import meraki, config

api_key = config.api_key
org_id = config.org_id
uplink1 = config.uplink1

#EXCLUDE MONITORING THESE IPS, USUALLY ANY VPN ADDRESSES
ipToExclude  = ['8.8.8.8','8.8.4.4','1.1.1.1','208.67.220.220','208.67.222.222']

while True:
    previousNetwork = ""
    
    #GET UPLINK LATENCY AND LOSS INFO FOR ALL MONITORED IPS IN ALL NETWORKS
    orgloss = meraki.getorguplinklosslatency(api_key, org_id, uplink1)
    for network in orgloss:
        
        tagsAfter = [] #ARRAY WITH FINAL TAGS
        tagsString = "" #STRING WITH FINAL TAGS
        #ONLY PERFORM ONE ACTION PER NETWORK (IN CASE OF MULTIPLE MONITORED IPS)
        if network['ip'] not in ipToExclude and network['networkId'] != previousNetwork:
            
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
                    
            #GET UPLINK STATUS FOR WAN 1, TO MONITOR FOR UPLINK DOWN
            uplinks_status = meraki.getdeviceuplink(api_key, network['networkId'], network['serial'])
            uplink_status = ''
            for uplink in uplinks_status:
                if uplink['interface'] == config.interface1:
                    uplink_status = uplink['status']
            print("Uplink Status for "+config.interface1+" : "+uplink_status)
            
            #CHECK CONNECTIVITY HEALTH, IF UNDERPERFORMING OR UPLINK DOWN, SWAP PRIMARY AND BACKUP TAGS, AND ADD tcr_swapped TAG
            for iteration in network['timeSeries']:
                if iteration['lossPercent'] >= 30 or iteration['latencyMs'] >= 100 or uplink_status is not 'Active':
                    loss=True
                    if swapped == True:
                        print("VPN already swapped")
                        break
                    else:
                        print("Need to change VPN, recent loss - "+str(iteration['lossPercent'])+"% - "+str(iteration['latencyMs'])+"ms")
                        tagsAfter.append(primary.split("_up")[0]+"_down")
                        tagsAfter.append(backup.split("_down")[0]+"_up")
                        tagsAfter.append("tcr_swapped")
                        for tag in tagsAfter:
                            tagsString+= tag + " "
                        print("New List of Tags : "+tagsString)
                        new_network_info = meraki.updatenetwork(api_key, network['networkId'], tags=tagsAfter)
                        break
            
            #IF HEALTH RESTORED, SWAP TAGS BACK
            if loss==False and swapped == True:
                print("Primary VPN healthy again..Swapping back")
                tagsAfter.append(primary.split("_down")[0]+"_up")
                tagsAfter.append(backup.split("_up")[0]+"_down")
                for tag in tagsAfter:
                    tagsString+= tag + " "
                print("New List of Tags : "+tagsString)
                new_network_info = meraki.updatenetwork(api_key, network['networkId'], tags=tagsAfter)
        previousNetwork = network['networkId']
    print("Sleeping for 5s...")
    print("#####################################")
    print("#####################################")
    time.sleep(5)
