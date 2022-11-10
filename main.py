import os
import logging
from time import sleep
from typing import Optional
from datetime import datetime
import httpx
from dotenv import load_dotenv
import obsws_python as obs
from dataclassies import EPG


logger = logging.Logger('obs-epg-recording')

class Environments():
    def __init__(self) -> None:
        load_dotenv()
        self.host_name = os.getenv('HOST_NAME')
        self.port = os.getenv('PORT')
        self.password = os.getenv('PASSWORD')


class OBSClient():
    @classmethod
    def load(cls, host_name: str, port: str, password: str = None) -> obs.ReqClient:
        return obs.ReqClient(host=host_name, port=port, password=password)


URL = 'http://192.168.1.100:8888'
class EPGStation():
    def __init__(self) -> None:
        pass

    def get_atx_reserve() -> Optional[EPG]:
        ATX_CHANNEL_ID = 6553400605
        result = httpx.get(f'{URL}/api/reserves?isHalfWidth=true&limit=100')
        atx_reserves = list(filter(lambda x: x['channelId'] == ATX_CHANNEL_ID, result.json().get('reserves')))
        return EPG(
            id=atx_reserves[0]['id'],
            name=atx_reserves[0]['name'],
            start_at=atx_reserves[0]['startAt'],
            end_at=atx_reserves[0]['endAt']
        ) if atx_reserves else None


class EPGRecoding():

    def run(self):
        """Main."""
        env = Environments()
        # OBS
        self.obs_client = OBSClient.load(env.host_name, env.port, env.password)

        while True:
            atx_reserve = EPGStation.get_atx_reserve()

            # If no recording is reserved, standby for 1 hour
            if atx_reserve is None:
                sleep(3600)
                continue

            if self.wait_for_program_to_start(atx_reserve):
                continue
            else:
                print(f'Start recording {atx_reserve.name}')
                self._start_record()
                end_at = datetime.fromtimestamp(atx_reserve.end_at/1000) - datetime.now()
                sleep(end_at.total_seconds())
                self._stop_record()
                print(f'End recording {atx_reserve.name}')


    def wait_for_program_to_start(self, epg: EPG) -> bool:
        """Wait for the program to start.

        Args:
            epg (EPG): program data

        Returns:
            bool: If still need to wait, True
        """
        start_at = datetime.fromtimestamp(epg.start_at/1000)
        wait_time = start_at - datetime.now()
        if wait_time.total_seconds() > 3610:
            print(f'Wait for the start of {epg.name} {start_at}')
            sleep(3600)
            return True
        elif wait_time.total_seconds() > 10:
            print(f'Wait for the start of {epg.name} {start_at}')
            sleep(wait_time.total_seconds() - 10)
            return False
        else:
            return False


    def _set_scene(self, scene_name: str):
        # scene_name = 'Mirabox AT-X'
        return self.obs_client.scene(scene_name)


    def _start_record(self):
        """Recording start."""
        self.obs_client.start_record()


    def _stop_record(self):
        """Recording stop."""
        self.obs_client.stop_record()
        sleep(5) # interval


if __name__ == '__main__':
    EPGRecoding().run()
