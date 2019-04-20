from Memory import *
import time, os
from threading import Thread
import psutil

class IDS:
    NoMonstersZones = [0, 3.1, 5, 7, 11, 15, 23, 24, 31]
    Zones = {
        3 : "Great Ravine",
        3.1 : "Main Menu",
        5 : "Main Menu",
        7 : "Main Menu",
        17 : "Main Menu",
        8 : "Special Arena",
        10 : "Confluence of Fates",
        11 : "Gathering HUB",
        12 : "Caverns of El Dorado",
        15 : "My Room",
        18 : "Elder's Recess",
        23 : "Training area",
        23.1 : "Arena",
        24 : "Research Base",
        31 : "Astera",
        37 : "Rotten Vale",
        58 : "Coral Highlands",
        64 : "Wildspire Waste",
        94 : "Ancient Forest",
    }
    Monsters = {
        "em100_00" : "Anjanath",
        "em002_01" : "Azure Rathalos",
        "em044_00" : "Barroth",
        "em118_00" : "Bazelgeuse",
        "em121_00" : "Behemoth",
        "em007_01" : "Black Diablos",
        "em043_00" : "Deviljho",
        "em007_00" : "Diablos",
        "em116_00" : "Dodogama",
        "em112_00" : "Great Girros",
        "em108_00" : "Jyuratodus",
        "em011_00" : "Kirin",
        "em107_00" : "Kulu Ya Ku",
        "em117_00" : "Kulve Taroth",
        "em024_00" : "Kushala Daora",
        "em036_00" : "Lavasioth",
        "em111_00" : "Legiana",
        "em026_00" : "Lunastra",
        "em103_00" : "Nergigante",
        "em113_00" : "Odogaron",
        "em110_00" : "Paolumu",
        "em001_01" : "Pink Rathian",
        "em102_00" : "Pukei Pukei",
        "em114_00" : "Radobaan",
        "em002_00" : "Rathalos",
        "em001_00" : "Rathian",
        "em027_00" : "Teostra",
        "em109_00" : "Tobi Kadachi",
        "em120_00" : "TziTzi Ya Ku",
        "em045_00" : "Uragaan",
        "em115_00" : "Vaal Hazak",
        "em105_00" : "Xeno'Jiiva",
        "em106_00" : "Zorah Magdaros"
    }


class Player:
    def __init__(self):
        self.Name = ""
        self.Level = 0
        self.ZoneID = 0
        self.LastZoneID = 0
        self.ZoneName = ""
        self.SessionID = ""
        

class Monster:
    def __init__(self):
        self.Name = "UNKNOWN"
        self.Id = ""
        self.TotalHP = 0
        self.CurrentHP = 0
        self.isTarget = False
        self.Address = 0x0

class Game:
    baseAddress = 0x140000000 # MonsterHunterWorld.exe base address
    LevelOffset = 0x3B5FEC8    # Level offset
    levelAddress = 0xFFFFFF     # Level address used to get name
    ZoneOffset = 0x04852910  # Zone ID offset
    MonsterOffset = 0x48525D0 # monster offset
    SessionOffset = 0x0485A430 # Session id offset
    
    def __init__(self, pid):
        # Scanner stuff
        self.pid = pid
        self.MemoryReader = Memory(self.pid)
        self.Scanner = False
        # Player info
        self.PlayerInfo = Player()
        # Monsters info
        self.PrimaryMonster = Monster()
        self.SecondaryMonster = Monster()
        self.ThirtiaryMonster = Monster()
        self.Logger = []
        
    def scanUntilDone(self):
        while psutil.pid_exists(self.pid):
            self.Logger = []
            self.getPlayerLevel()
            self.getPlayerName()
            self.getSessionID()
            #self.Logger.append(f"{self.PlayerInfo.LastZoneID} -> {self.PlayerInfo.ZoneID}\n")
            self.GetAllMonstersAddress()
            self.GetAllMonstersInfo()
            self.getPlayerZoneID()
            self.PredictTarget()
            
            time.sleep(0.2)

    def MultiThreadScan(self):
        self.Scanner = Thread(target=self.scanUntilDone)
        self.Scanner.daemon = True
        self.Scanner.start()

    def init(self):
        self.Logger.append(f"BASE ADDRESS: {hex(Game.baseAddress)}")
        self.MultiThreadScan()
            
    def getPlayerName(self):
        self.PlayerInfo.Name = self.MemoryReader.readString(Game.levelAddress-64, 20).decode().strip('\x00')
        self.Logger.append(f"PLAYER NAME: {self.PlayerInfo.Name} ({hex(Game.levelAddress-64)})\n")

    def getPlayerLevel(self):
        Address = Game.baseAddress + Game.LevelOffset
        fValue = self.MemoryReader.readInteger(Address)
        ptrAddress = fValue + 144
        ptrValue = self.MemoryReader.readInteger(ptrAddress)
        Game.levelAddress = ptrValue + 0x68
        self.PlayerInfo.Level = self.MemoryReader.readInteger(ptrValue + 0x68)
        self.Logger.append(f'HUNTER RANK: {self.PlayerInfo.Level} ({hex(ptrValue+0x68)})\n')

    def getPlayerZoneID(self):
        Address = Game.baseAddress + Game.ZoneOffset
        offsets = [0x78, 0x440, 0x8, 0x70]
        sValue = self.MemoryReader.GetMultilevelPtr(Address, offsets)
        ZoneID = self.MemoryReader.readInteger(sValue + 0x2B0)
        if ZoneID == 23 and self.ThirtiaryMonster.TotalHP != 100: # Checks if there's a monster in the map, if so then it's an arena
            ZoneID = 23.1
        if ZoneID == 3 and self.SecondaryMonster.TotalHP == 0:
            ZoneID = 3.1
        if self.PlayerInfo.ZoneID != ZoneID:
            self.UpdateLastZoneID()
            self.PlayerInfo.ZoneID = ZoneID
        self.getPlayerZoneNameByID()
        self.Logger.insert(2, f'{self.PlayerInfo.ZoneName} | ZONE ID: {self.PlayerInfo.ZoneID} ({hex(sValue + 0x2B0)})\n')
        
    def getPlayerZoneNameByID(self):
        self.PlayerInfo.ZoneName = IDS.Zones.get(self.PlayerInfo.ZoneID)

    def GetAllMonstersAddress(self):
        AddressBase = Game.baseAddress + Game.MonsterOffset
        offsets = [0xAF738, 0x47CDE0]
        thirdMonsterAddress = self.MemoryReader.GetMultilevelPtr(AddressBase, offsets)
        thirdMonsterAddress = self.MemoryReader.readInteger(thirdMonsterAddress + 0x0)
        thirdMonsterAddress = thirdMonsterAddress + 0x0
        secondMonsterAddress = thirdMonsterAddress + 0x28
        firstMonsterAddress = self.MemoryReader.readInteger(secondMonsterAddress) + 0x28
        self.PrimaryMonster.Address = firstMonsterAddress
        self.SecondaryMonster.Address = secondMonsterAddress
        self.ThirtiaryMonster.Address = thirdMonsterAddress

    # GET ALL MONSTER INFO
    def GetAllMonstersInfo(self):
        self.GetAllMonstersName()
        self.GetAllMonstersID()
        self.GetAllMonstersHP()

    ## GET ALL MONSTERS NAME
    def GetAllMonstersName(self):
        self.PrimaryMonster.Name = IDS.Monsters.get(self.PrimaryMonster.Id)
        self.SecondaryMonster.Name = IDS.Monsters.get(self.SecondaryMonster.Id)
        self.ThirtiaryMonster.Name = IDS.Monsters.get(self.ThirtiaryMonster.Id)

    ## GET ALL MONSTERS HP
    def GetAllMonstersHP(self):
        try:
            self.getFirstMonsterTotalHP()
        except:
            pass
        try:
            self.getSecondMonsterTotalHP()
        except:
            pass
        try:
            self.getThirtiaryMonsterTotalHP()
        except:
            pass
        

    ## GET ALL MONSTERS ID
    def GetAllMonstersID(self):
        try:
            self.GetFirstMonsterID()
        except:
            self.PrimaryMonster.Id = None
            pass
        try:
            self.GetSecondMonsterID()
        except:
            self.SecondaryMonster.Id = None
            pass
        try:
            self.GetThirdMonsterID()
        except:
            self.ThirtiaryMonster.Id = None
            pass
        
    ## Get 1st info
    def GetFirstMonsterID(self):
        Address = self.PrimaryMonster.Address
        Address = self.MemoryReader.readInteger(Address)
        namePointer = self.MemoryReader.readInteger(Address + 0x290)
        Id = self.MemoryReader.readString(namePointer + 0x0c, 64).decode().split('\\')[4].strip('\x00')
        self.PrimaryMonster.Id = Id

    def getFirstMonsterTotalHP(self):
        Address = self.PrimaryMonster.Address
        Address = self.MemoryReader.readInteger(Address)
        monsterHPComponent = self.MemoryReader.readInteger(Address+0x129D8+0x48)
        monsterTotalHpAddress = monsterHPComponent + 0x60
        monsterTotalHP = self.MemoryReader.readFloat(monsterTotalHpAddress)
        if self.PrimaryMonster.Id != None and self.PrimaryMonster.Id.startswith('ems'):
            self.PrimaryMonster.TotalHP = 0
        else:
            self.PrimaryMonster.TotalHP = monsterTotalHP
        self.getPrimaryMonsterCurrentHP(monsterTotalHpAddress)
        self.Logger.append(f'NAME: {self.PrimaryMonster.Name} | ID: {self.PrimaryMonster.Id} | HP: {int(self.PrimaryMonster.CurrentHP)}/{int(self.PrimaryMonster.TotalHP)} ({hex(monsterTotalHpAddress)})\n')
        self.Logger.append(f"Target: {self.PrimaryMonster.isTarget}\n")

    def getPrimaryMonsterCurrentHP(self, totalHPAddress):
        TotalHP = self.MemoryReader.readFloat(totalHPAddress)
        currentHP = self.MemoryReader.readFloat(totalHPAddress + 0x4)
        self.PrimaryMonster.CurrentHP = currentHP if currentHP <= self.PrimaryMonster.TotalHP else 0

    ## Get 2nd info
    def GetSecondMonsterID(self):
        Address = self.SecondaryMonster.Address
        Address = self.MemoryReader.readInteger(Address)
        namePointer = self.MemoryReader.readInteger(Address + 0x290)
        Id = self.MemoryReader.readString(namePointer + 0x0c, 64).decode().split('\\')[4].strip('\x00')
        self.SecondaryMonster.Id = Id

    def getSecondMonsterTotalHP(self):
        Address = self.SecondaryMonster.Address
        Address = self.MemoryReader.readInteger(Address)
        monsterHPComponent = self.MemoryReader.readInteger(Address+0x129D8+0x48)
        monsterTotalHPAddress = monsterHPComponent + 0x60
        monsterTotalHP = self.MemoryReader.readFloat(monsterTotalHPAddress)
        if self.SecondaryMonster.Id != None and self.SecondaryMonster.Id.startswith('ems'):
            self.SecondaryMonster.TotalHP = 0
        else:
            self.SecondaryMonster.TotalHP = monsterTotalHP
        self.getSecondaryMonsterCurrentHP(monsterTotalHPAddress)
        self.Logger.append(f'NAME: {self.SecondaryMonster.Name} | ID: {self.SecondaryMonster.Id} | HP: {int(self.SecondaryMonster.CurrentHP)}/{int(self.SecondaryMonster.TotalHP)} ({hex(monsterTotalHPAddress)})\n')
        self.Logger.append(f"Target: {self.SecondaryMonster.isTarget}\n")

    def getSecondaryMonsterCurrentHP(self, totalHPAddress):
        TotalHP = self.MemoryReader.readFloat(totalHPAddress)
        currentHp = self.MemoryReader.readFloat(totalHPAddress + 0x4)
        self.SecondaryMonster.CurrentHP = currentHp if currentHp <= self.SecondaryMonster.TotalHP else 0

    ## Get 3rd info
    def GetThirdMonsterID(self):
        Address = self.ThirtiaryMonster.Address
        namePointer = self.MemoryReader.readInteger(Address + 0x290)
        Id = self.MemoryReader.readString(namePointer + 0x0c, 64).decode().split('\\')[4].strip('\x00')
        self.ThirtiaryMonster.Id = Id

    def getThirtiaryMonsterTotalHP(self):
        Address = self.ThirtiaryMonster.Address
        monsterHPComponent = self.MemoryReader.readInteger(Address+0x129D8+0x48)
        monsterTotalHPAddress = monsterHPComponent + 0x60
        monsterTotalHP = self.MemoryReader.readFloat(monsterTotalHPAddress)
        self.getThirtiaryMonsterCurrentHP(monsterTotalHPAddress)
        self.ThirtiaryMonster.TotalHP = int(monsterTotalHP)
        self.Logger.append(f'NAME: {self.ThirtiaryMonster.Name} | ID: {self.ThirtiaryMonster.Id} | HP: {int(self.ThirtiaryMonster.CurrentHP)}/{int(self.ThirtiaryMonster.TotalHP)} ({hex(monsterTotalHPAddress)})\n')
        self.Logger.append(f"Target: {self.ThirtiaryMonster.isTarget}\n")

    def getThirtiaryMonsterCurrentHP(self, totalHPAddress):
        TotalHP = self.MemoryReader.readFloat(totalHPAddress)
        currentHP = self.MemoryReader.readFloat(totalHPAddress + 0x4)
        self.ThirtiaryMonster.CurrentHP =  int(currentHP) if TotalHP >= int(currentHP) else 0

    # Session ID
    def getSessionID(self):
        Address = Game.baseAddress + Game.SessionOffset
        offsets = [0xA0, 0x20, 0x80, 0x9C]
        sValue = self.MemoryReader.GetMultilevelPtr(Address, offsets)
        SessionID = self.MemoryReader.readString(sValue+0x3C8, 12)
        self.PlayerInfo.SessionID = SessionID.decode()
        self.Logger.append(f'Session ID: {self.PlayerInfo.SessionID} ({hex(sValue+0x3C8)})\n')

    ## Zones
    def UpdateLastZoneID(self):
        self.PlayerInfo.LastZoneID = self.PlayerInfo.ZoneID 

    # Since I have no idea how to detect which monster is being targetted
    # I'm gonna just make this workaround.
    def PredictTarget(self):
        if self.PlayerInfo.ZoneID in IDS.NoMonstersZones:
            self.PrimaryMonster.isTarget = False
            self.SecondaryMonster.isTarget = False
            self.ThirtiaryMonster.isTarget = False
            return
        if self.ThirtiaryMonster.TotalHP > 0:
            tMonsterPercentage = self.ThirtiaryMonster.CurrentHP / self.ThirtiaryMonster.TotalHP if (self.ThirtiaryMonster.CurrentHP / self.ThirtiaryMonster.TotalHP) > 0 else 1
        else:
            tMonsterPercentage = 1
        if self.SecondaryMonster.TotalHP > 0:
            sMonsterPercentage = self.SecondaryMonster.CurrentHP / self.SecondaryMonster.TotalHP if (self.SecondaryMonster.CurrentHP / self.SecondaryMonster.TotalHP) > 0 else 1
        else:
            sMonsterPercentage = 1
        if self.PrimaryMonster.TotalHP > 0:
            fMonsterPercentage = self.PrimaryMonster.CurrentHP / self.PrimaryMonster.TotalHP if (self.PrimaryMonster.CurrentHP / self.PrimaryMonster.TotalHP) > 0 else 1
        else:
            fMonsterPercentage = 1
        monsterHealthPercentage = [tMonsterPercentage, sMonsterPercentage, fMonsterPercentage]
        for health in sorted(monsterHealthPercentage):
            if health < 1:
                if health == tMonsterPercentage:
                    self.PrimaryMonster.isTarget = False
                    self.SecondaryMonster.isTarget = False
                    self.ThirtiaryMonster.isTarget = True
                    return
                elif health == sMonsterPercentage:
                    self.PrimaryMonster.isTarget = False
                    self.SecondaryMonster.isTarget = True
                    self.ThirtiaryMonster.isTarget = False
                    return
                elif health == fMonsterPercentage:
                    self.PrimaryMonster.isTarget = True
                    self.SecondaryMonster.isTarget = False
                    self.ThirtiaryMonster.isTarget = False
                    return
                else:
                    self.PrimaryMonster.isTarget = False
                    self.SecondaryMonster.isTarget = False
                    self.ThirtiaryMonster.isTarget = False
                    return
            elif health == 1:
                self.PrimaryMonster.isTarget = False
                self.SecondaryMonster.isTarget = False
                self.ThirtiaryMonster.isTarget = False
                continue
