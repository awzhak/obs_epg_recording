import os
from time import sleep
from typing import List, Optional
from datetime import datetime
import httpx
from dotenv import load_dotenv
import obsws_python as obs
from dataclassies import EPG
from logger import logger


class Environments():
    def __init__(self) -> None:
        load_dotenv()
        self.host_name = os.getenv('HOST_NAME')
        self.port = os.getenv('PORT')
        self.password = os.getenv('PASSWORD')


class OBSClient():
    @classmethod
    def load(cls, host_name: str, port: str, password: Optional[str] = None) -> obs.ReqClient:
        return obs.ReqClient(host=host_name, port=port, password=password)


class EPGStation():
    def __init__(self) -> None:
        pass

    @classmethod
    def get_atx_reserves(cls) -> Optional[List[EPG]]:
        ATX_CHANNEL_ID = 6553400605
        result = httpx.get('http://192.168.1.100:8888/api/reserves?isHalfWidth=true&limit=100')
        atx_reserves = list(filter(lambda x: x['channelId'] == ATX_CHANNEL_ID, result.json().get('reserves')))
        return [EPG(
            id=atx_reserve['id'],
            name=atx_reserve['name'],
            start_at=atx_reserve['startAt'],
            end_at=atx_reserve['endAt'],
        ) for atx_reserve in atx_reserves] if atx_reserves else None


class EPGRecoding():

    def run(self):
        """Main."""
        env = Environments()
        # OBS
        self.obs_client = OBSClient.load(env.host_name, env.port, env.password)

        while True:
            atx_reserves = EPGStation.get_atx_reserves()
            atx_reserve = self.find_reservations_to_record_next(atx_reserves)
            # If no recording is reserved, standby for 1 hour
            if atx_reserve is None:
                sleep(3600)
                continue

            if self.wait_for_program_to_start(atx_reserve):
                continue

            logger.info(f'Start recording {atx_reserve.name}')
            self._start_record()
            end_at = datetime.fromtimestamp(atx_reserve.end_at/1000) - datetime.now()
            sleep(end_at.total_seconds() - 10)
            self._stop_record()
            logger.info(f'End recording {atx_reserve.name}')
            sleep(5)  # interval

    def find_reservations_to_record_next(self, reserves: List[EPG]) -> Optional[EPG]:
        if reserves is None:
            return None

        end_at = datetime.fromtimestamp(reserves[0].end_at/1000)
        end_wait_time = end_at - datetime.now()
        if end_wait_time.total_seconds() > 10:
            return reserves[0]
        else:
            return reserves[1] if len(reserves) > 1 else None

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
            logger.info(f'Wait for the start of {epg.name} at {start_at}')
            sleep(3600)
            return True
        elif wait_time.total_seconds() > 10:
            logger.info(f'Wait for the start of {epg.name} at {start_at}')
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


if __name__ == '__main__':
    try:
        EPGRecoding().run()
    except KeyboardInterrupt:
        logger.info('Exit obg-epg-recording')
