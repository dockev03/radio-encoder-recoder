import socket
import time

import psutil


# Dernier relevé des compteurs réseau.
#
# On conserve ces valeurs en mémoire afin de calculer
# le débit entre deux appels de get_network_status().
_network_samples = {}


def _calculate_network_speed(
    interface_name,
    bytes_recv,
    bytes_sent
):
    """
    Calcule les débits RX/TX en bits par seconde
    pour une interface réseau.
    """

    now = time.monotonic()

    previous = _network_samples.get(
        interface_name
    )

    _network_samples[interface_name] = {
        "time": now,
        "bytes_recv": bytes_recv,
        "bytes_sent": bytes_sent
    }

    # Premier relevé :
    # impossible de calculer un débit.
    if previous is None:

        return {
            "download_bps": 0,
            "upload_bps": 0
        }


    elapsed = (
        now -
        previous["time"]
    )


    if elapsed <= 0:

        return {
            "download_bps": 0,
            "upload_bps": 0
        }


    received_difference = max(
        0,
        bytes_recv -
        previous["bytes_recv"]
    )


    sent_difference = max(
        0,
        bytes_sent -
        previous["bytes_sent"]
    )


    # Les compteurs psutil sont en octets.
    # On multiplie par 8 pour obtenir des bits/s.

    download_bps = (
        received_difference *
        8 /
        elapsed
    )


    upload_bps = (
        sent_difference *
        8 /
        elapsed
    )


    return {
        "download_bps":
            round(download_bps),

        "upload_bps":
            round(upload_bps)
    }


def get_network_status():
    """
    Retourne l'état de la connexion réseau principale.

    On cherche une interface :
    - active
    - différente de loopback
    - possédant une adresse IPv4

    Le débit RX/TX est calculé uniquement
    pour cette interface.
    """

    try:

        interfaces = (
            psutil.net_if_stats()
        )

        addresses = (
            psutil.net_if_addrs()
        )

        counters = (
            psutil.net_io_counters(
                pernic=True
            )
        )


        for (
            interface_name,
            stats
        ) in interfaces.items():

            if interface_name == "lo":
                continue


            if not stats.isup:
                continue


            interface_addresses = (
                addresses.get(
                    interface_name,
                    []
                )
            )


            ipv4_address = None


            for address in interface_addresses:

                if (
                    address.family ==
                    socket.AF_INET
                ):

                    ipv4_address = (
                        address.address
                    )

                    break


            if ipv4_address is None:
                continue


            interface_counters = (
                counters.get(
                    interface_name
                )
            )


            download_bps = 0
            upload_bps = 0


            if (
                interface_counters
                is not None
            ):

                speeds = (
                    _calculate_network_speed(
                        interface_name,
                        interface_counters.bytes_recv,
                        interface_counters.bytes_sent
                    )
                )


                download_bps = (
                    speeds[
                        "download_bps"
                    ]
                )


                upload_bps = (
                    speeds[
                        "upload_bps"
                    ]
                )


            return {
                "connected": True,
                "interface":
                    interface_name,
                "ip":
                    ipv4_address,
                "download_bps":
                    download_bps,
                "upload_bps":
                    upload_bps
            }


    except Exception:
        pass


    return {
        "connected": False,
        "interface": None,
        "ip": None,
        "download_bps": 0,
        "upload_bps": 0
    }


def get_system_status():

    temperature = None


    try:

        temperatures = (
            psutil
            .sensors_temperatures()
        )


        if temperatures:

            for entries in (
                temperatures.values()
            ):

                if entries:

                    temperature = round(
                        entries[0].current,
                        1
                    )

                    break


    except Exception:
        pass


    return {
        "cpu":
            psutil.cpu_percent(),

        "ram":
            psutil
            .virtual_memory()
            .percent,

        "temperature":
            temperature,

        "uptime":
            int(
                time.time()
                -
                psutil.boot_time()
            )
    }