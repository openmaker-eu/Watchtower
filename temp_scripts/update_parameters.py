from application.Connections import Connection
from pdb import set_trace
def updateAudienceParameters(topicID, location, signal_strength):
    with Connection.Instance().get_cursor() as cur:
        sql = (
                "UPDATE audience_parameters "
                "SET signal_strength = %s "
                "WHERE topic_id = %s and location = %s  "
            )
        cur.execute(sql, [int(signal_strength), int(topicID), location])

def updateInfluencerParameters(topicID, location, signal_strength, following_limit):
    with Connection.Instance().get_cursor() as cur:
        sql = (
                "UPDATE influencer_parameters "
                "SET signal_strength = %s, following_limit = %s "
                "WHERE topic_id = %s and location = %s  "
            )
        cur.execute(sql, [int(signal_strength), int(following_limit), int(topicID), location])


print("Influencer or Audience ?\n1) Influencer\n2) Audience")
choice = int(input())
if choice == 1:
    # Influencer
    s = ""
    
    print("Enter 'topicID, location, signal_strength, following_limit' and press enter.\nType 'DONE' to finish.")
    s = input()
    while(s != "DONE"):
        l = s.strip().split()
        if(len(l) == 4):
            updateInfluencerParameters(*l)
            print("UPDATED!")
        s = input()
if choice == 2:
    # Audience
    s = ""
    
    print("Enter 'topicID, location, signal_strength' and press enter.\nType 'DONE' to finish.")
    s = input()
    while(s != "DONE"):
        l = s.strip().split()
        if(len(l) == 3):
            updateAudienceParameters(*l)
            print("UPDATED!")
        s = input()
