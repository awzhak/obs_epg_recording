import os
from dotenv import load_dotenv
import obsws_python as obs


class Environments():
    def __init__(self) -> None:
        load_dotenv()
        self.host_name = os.getenv('HOST_NAME')
        self.port = os.getenv('PORT')
        self.password = os.getenv('PASSWORD')


class OBSClient():

    @classmethod
    def load(cls, host_name: str, port: int, password: str = None) -> obs.ReqClient:
        return obs.ReqClient(host=host_name, port=port, password=password)


class CaptureBoardRecoding():

    def run(self):
        """Main."""
        # OBS
        self.env = Environments()
        self.obs_client: obs.ReqClient = OBSClient.load(host_name=self.env.host_name,
                                                        port=int(self.env.port),
                                                        password=self.env.password)

        # Recording
        self._start_record()


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
    CaptureBoardRecoding().run()
