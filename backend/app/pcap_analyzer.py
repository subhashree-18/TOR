"""
PCAP File Analyzer for TOR Unveil
Extracts packet metadata and correlates with TOR paths
"""

import struct
import logging
from typing import List, Dict, Any, Tuple, Optional
import datetime
from io import BytesIO

logger = logging.getLogger("tor_unveil.pcap")

# PCAP Global Header Structure
PCAP_GLOBAL_HEADER = struct.Struct('<IHHIIII')  # Little-endian format
PCAP_PACKET_HEADER = struct.Struct('<IIII')

# Magic numbers for PCAP file format detection
PCAP_MAGIC_LE = 0xa1b2c3d4  # Little-endian
PCAP_MAGIC_BE = 0xd4c3b2a1  # Big-endian
PCAP_MAGIC_LE_NS = 0xa1b23c4d  # Little-endian with nanoseconds
PCAP_MAGIC_BE_NS = 0x4d3cb2a1  # Big-endian with nanoseconds

# Link layer types
LINK_TYPE_ETHERNET = 1
LINK_TYPE_RAW = 7
LINK_TYPE_LOOP = 108

# IP protocol types
IP_PROTO_TCP = 6
IP_PROTO_UDP = 17
IP_PROTO_ICMP = 1

# Ethernet frame structure
ETH_HEADER_LEN = 14
ETH_TYPE_IPV4 = 0x0800
ETH_TYPE_IPV6 = 0x86DD

# IPv4 header structure
IPV4_MIN_HEADER = 20

# TCP/UDP header structure
TCP_HEADER_MIN = 20
UDP_HEADER_LEN = 8


class PCAPAnalyzer:
    """Parses PCAP files and extracts network metadata"""
    
    def __init__(self, data: bytes):
        """Initialize PCAP analyzer with file data
        
        Args:
            data: Raw bytes of PCAP file
        """
        self.data = data
        self.offset = 0
        self.packets = []
        self.metadata = {}
        self.is_valid = False
        self.byte_order = None
        self.nanosecond_precision = False
        
    def parse(self) -> Dict[str, Any]:
        """Parse PCAP file and extract metadata
        
        Returns:
            Dictionary with:
            - success: bool indicating successful parse
            - total_packets: number of packets
            - packets: list of parsed packets
            - metadata: file metadata
            - time_range: min/max timestamps
            - protocols: protocol distribution
            - ips: unique IPs
            - ports: port usage
        """
        try:
            if len(self.data) < 24:
                logger.error("PCAP file too small (< 24 bytes)")
                return {
                    'success': False,
                    'error': 'File too small to be valid PCAP',
                    'size': len(self.data)
                }
            
            # Read global header
            if not self._parse_global_header():
                return {
                    'success': False,
                    'error': 'Invalid PCAP global header or unsupported magic number',
                    'first_bytes': self.data[:8].hex()
                }
            
            logger.info(f"PCAP file validated. Byte order: {'LE' if self.byte_order == '<' else 'BE'}")
            
            # Parse packets
            self._parse_packets()
            
            # Analyze results
            analysis = self._analyze_packets()
            
            return {
                'success': True,
                'total_packets': len(self.packets),
                'packets': self.packets[:1000],  # Limit to first 1000 for response
                'metadata': self.metadata,
                'analysis': analysis,
                'time_range': self._get_time_range(),
                'protocols': self._analyze_protocols(),
                'flows': self._analyze_flows(),
                'statistics': {
                    'total_packets': len(self.packets),
                    'total_bytes': sum(p.get('captured_len', 0) for p in self.packets),
                    'unique_ips': analysis['unique_ips'],
                    'unique_ports': analysis['unique_ports'],
                }
            }
            
        except Exception as e:
            logger.error(f"PCAP parse error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'PCAP parsing failed: {str(e)}'
            }
    
    def _parse_global_header(self) -> bool:
        """Parse PCAP global header
        
        Returns:
            True if valid header found
        """
        if len(self.data) < 24:
            return False
        
        # Try little-endian first (most common)
        magic_le, = struct.unpack_from('<I', self.data, 0)
        magic_be, = struct.unpack_from('>I', self.data, 0)
        
        # Detect byte order and nanosecond precision
        if magic_le == PCAP_MAGIC_LE:
            self.byte_order = '<'
            self.nanosecond_precision = False
            logger.debug("Detected little-endian PCAP (microsecond)")
        elif magic_le == PCAP_MAGIC_LE_NS:
            self.byte_order = '<'
            self.nanosecond_precision = True
            logger.debug("Detected little-endian PCAP (nanosecond)")
        elif magic_be == PCAP_MAGIC_BE:
            self.byte_order = '>'
            self.nanosecond_precision = False
            logger.debug("Detected big-endian PCAP (microsecond)")
        elif magic_be == PCAP_MAGIC_BE_NS:
            self.byte_order = '>'
            self.nanosecond_precision = True
            logger.debug("Detected big-endian PCAP (nanosecond)")
        else:
            logger.error(f"Invalid PCAP magic number: LE={magic_le:#010x}, BE={magic_be:#010x}")
            return False
        
        # Parse global header fields
        fmt = self.byte_order + 'IHHIIII'
        header = struct.unpack_from(fmt, self.data, 0)
        
        magic_num, version_major, version_minor, tzoffset, ts_accuracy, snapshot_len, link_type = header
        
        self.metadata = {
            'magic': hex(magic_num),
            'version': f"{version_major}.{version_minor}",
            'tz_offset': tzoffset,
            'timestamp_accuracy': ts_accuracy,
            'snapshot_length': snapshot_len,
            'link_type': link_type,
            'link_type_name': self._get_link_type_name(link_type)
        }
        
        self.offset = 24
        self.is_valid = True
        return True
    
    def _parse_packets(self):
        """Parse all packets in PCAP file"""
        packet_count = 0
        
        while self.offset + 16 <= len(self.data):
            try:
                # Read packet header
                fmt = self.byte_order + 'IIII'
                ts_sec, ts_usec, incl_len, orig_len = struct.unpack_from(fmt, self.data, self.offset)
                
                packet_header_len = 16
                self.offset += packet_header_len
                
                # Validate packet size
                if incl_len > self.metadata['snapshot_length']:
                    logger.warning(f"Packet {packet_count}: captured length {incl_len} exceeds snapshot")
                    incl_len = self.metadata['snapshot_length']
                
                if self.offset + incl_len > len(self.data):
                    logger.warning(f"Packet {packet_count}: truncated (need {incl_len}, have {len(self.data) - self.offset})")
                    break
                
                # Extract packet data
                packet_data = self.data[self.offset:self.offset + incl_len]
                self.offset += incl_len
                
                # Convert timestamp
                if self.nanosecond_precision:
                    timestamp = ts_sec + (ts_usec / 1e9)
                else:
                    timestamp = ts_sec + (ts_usec / 1e6)
                
                dt = datetime.datetime.utcfromtimestamp(timestamp)
                
                # Parse packet content
                packet_info = self._parse_packet_content(packet_data, dt, orig_len)
                
                if packet_info:
                    self.packets.append(packet_info)
                
                packet_count += 1
                
            except struct.error as e:
                logger.debug(f"Packet {packet_count}: struct unpack error: {e}")
                break
            except Exception as e:
                logger.debug(f"Packet {packet_count}: parse error: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(self.packets)} packets out of ~{packet_count} total")
    
    def _parse_packet_content(self, data: bytes, timestamp: datetime.datetime, 
                            orig_len: int) -> Optional[Dict[str, Any]]:
        """Parse packet content and extract metadata
        
        Args:
            data: Packet data bytes
            timestamp: Packet timestamp
            orig_len: Original packet length
            
        Returns:
            Dictionary with packet metadata or None
        """
        if len(data) < 1:
            return None
        
        packet = {
            'timestamp': timestamp.isoformat(),
            'captured_len': len(data),
            'original_len': orig_len,
            'link_type': self.metadata['link_type'],
        }
        
        offset = 0
        src_ip = None
        dst_ip = None
        src_port = None
        dst_port = None
        protocol = None
        
        try:
            # Parse based on link type
            if self.metadata['link_type'] == LINK_TYPE_ETHERNET:
                if len(data) < ETH_HEADER_LEN:
                    return packet  # Too short for Ethernet
                
                eth_type, = struct.unpack_from('>H', data, 12)
                offset = ETH_HEADER_LEN
                
                packet['eth_type'] = hex(eth_type)
                
                # Parse IPv4
                if eth_type == ETH_TYPE_IPV4:
                    src_ip, dst_ip, protocol = self._parse_ipv4(data[offset:])
                # Parse IPv6
                elif eth_type == ETH_TYPE_IPV6:
                    src_ip, dst_ip, protocol = self._parse_ipv6(data[offset:])
                    
            elif self.metadata['link_type'] == LINK_TYPE_RAW:
                # Raw IP
                if len(data) >= 1:
                    version = (data[0] >> 4) & 0xF
                    if version == 4:
                        src_ip, dst_ip, protocol = self._parse_ipv4(data)
                    elif version == 6:
                        src_ip, dst_ip, protocol = self._parse_ipv6(data)
            
            # Parse TCP/UDP ports
            if protocol == IP_PROTO_TCP:
                src_port, dst_port = self._parse_tcp_ports(data[offset:])
            elif protocol == IP_PROTO_UDP:
                src_port, dst_port = self._parse_udp_ports(data[offset:])
            
            # Store extracted information
            if src_ip:
                packet['src_ip'] = src_ip
            if dst_ip:
                packet['dst_ip'] = dst_ip
            if src_port:
                packet['src_port'] = src_port
            if dst_port:
                packet['dst_port'] = dst_port
            if protocol:
                packet['protocol'] = protocol
                packet['protocol_name'] = self._get_protocol_name(protocol)
            
            return packet
            
        except Exception as e:
            logger.debug(f"Error parsing packet content: {e}")
            return packet
    
    def _parse_ipv4(self, data: bytes) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Parse IPv4 header
        
        Returns:
            (src_ip, dst_ip, protocol)
        """
        if len(data) < IPV4_MIN_HEADER:
            return None, None, None
        
        try:
            version_ihl = data[0]
            ihl = (version_ihl & 0xF) * 4
            protocol = data[9]
            src_ip_bytes = data[12:16]
            dst_ip_bytes = data[16:20]
            
            src_ip = '.'.join(str(b) for b in src_ip_bytes)
            dst_ip = '.'.join(str(b) for b in dst_ip_bytes)
            
            return src_ip, dst_ip, protocol
            
        except Exception as e:
            logger.debug(f"IPv4 parse error: {e}")
            return None, None, None
    
    def _parse_ipv6(self, data: bytes) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Parse IPv6 header
        
        Returns:
            (src_ip, dst_ip, protocol)
        """
        if len(data) < 40:
            return None, None, None
        
        try:
            protocol = data[6]
            src_bytes = data[8:24]
            dst_bytes = data[24:40]
            
            src_ip = ':'.join(f"{int.from_bytes(src_bytes[i:i+2], 'big'):x}" 
                            for i in range(0, 16, 2))
            dst_ip = ':'.join(f"{int.from_bytes(dst_bytes[i:i+2], 'big'):x}" 
                            for i in range(0, 16, 2))
            
            return src_ip, dst_ip, protocol
            
        except Exception as e:
            logger.debug(f"IPv6 parse error: {e}")
            return None, None, None
    
    def _parse_tcp_ports(self, data: bytes) -> Tuple[Optional[int], Optional[int]]:
        """Parse TCP header for ports
        
        Returns:
            (src_port, dst_port)
        """
        if len(data) < TCP_HEADER_MIN:
            return None, None
        
        try:
            src_port, dst_port = struct.unpack('>HH', data[:4])
            return src_port, dst_port
        except Exception as e:
            logger.debug(f"TCP port parse error: {e}")
            return None, None
    
    def _parse_udp_ports(self, data: bytes) -> Tuple[Optional[int], Optional[int]]:
        """Parse UDP header for ports
        
        Returns:
            (src_port, dst_port)
        """
        if len(data) < UDP_HEADER_LEN:
            return None, None
        
        try:
            src_port, dst_port = struct.unpack('>HH', data[:4])
            return src_port, dst_port
        except Exception as e:
            logger.debug(f"UDP port parse error: {e}")
            return None, None
    
    def _analyze_packets(self) -> Dict[str, Any]:
        """Analyze parsed packets for statistics"""
        unique_ips = set()
        unique_ports = set()
        protocols = {}
        
        for packet in self.packets:
            if 'src_ip' in packet:
                unique_ips.add(packet['src_ip'])
            if 'dst_ip' in packet:
                unique_ips.add(packet['dst_ip'])
            if 'src_port' in packet:
                unique_ports.add(packet['src_port'])
            if 'dst_port' in packet:
                unique_ports.add(packet['dst_port'])
            
            protocol_name = packet.get('protocol_name', 'UNKNOWN')
            protocols[protocol_name] = protocols.get(protocol_name, 0) + 1
        
        return {
            'unique_ips': len(unique_ips),
            'unique_ports': len(unique_ports),
            'protocols': protocols
        }
    
    def _analyze_protocols(self) -> Dict[str, int]:
        """Analyze protocol distribution"""
        protocols = {}
        for packet in self.packets:
            protocol = packet.get('protocol_name', 'OTHER')
            protocols[protocol] = protocols.get(protocol, 0) + 1
        return protocols
    
    def _analyze_flows(self) -> List[Dict[str, Any]]:
        """Analyze network flows (IP pairs)"""
        flows = {}
        
        for packet in self.packets:
            src_ip = packet.get('src_ip', 'unknown')
            dst_ip = packet.get('dst_ip', 'unknown')
            protocol = packet.get('protocol_name', 'OTHER')
            
            if src_ip == 'unknown' or dst_ip == 'unknown':
                continue
            
            flow_key = (src_ip, dst_ip, protocol)
            
            if flow_key not in flows:
                flows[flow_key] = {
                    'src_ip': src_ip,
                    'dst_ip': dst_ip,
                    'protocol': protocol,
                    'packet_count': 0,
                    'byte_count': 0,
                    'ports': set(),
                    'first_seen': packet['timestamp'],
                    'last_seen': packet['timestamp']
                }
            
            flows[flow_key]['packet_count'] += 1
            flows[flow_key]['byte_count'] += packet.get('captured_len', 0)
            flows[flow_key]['last_seen'] = packet['timestamp']
            
            if 'src_port' in packet:
                flows[flow_key]['ports'].add(packet['src_port'])
            if 'dst_port' in packet:
                flows[flow_key]['ports'].add(packet['dst_port'])
        
        # Convert to list and format
        result = []
        for flow_key, flow_data in flows.items():
            flow_data['ports'] = list(flow_data['ports'])
            result.append(flow_data)
        
        return sorted(result, key=lambda x: x['packet_count'], reverse=True)[:100]
    
    def _get_time_range(self) -> Dict[str, Any]:
        """Get timestamp range of packets"""
        if not self.packets:
            return {'first': None, 'last': None, 'duration_seconds': 0}
        
        timestamps = [p.get('timestamp') for p in self.packets if p.get('timestamp')]
        if not timestamps:
            return {'first': None, 'last': None, 'duration_seconds': 0}
        
        return {
            'first': min(timestamps),
            'last': max(timestamps),
            'duration_seconds': 0  # Would need datetime parsing
        }
    
    @staticmethod
    def _get_link_type_name(link_type: int) -> str:
        """Get human-readable link type name"""
        names = {
            LINK_TYPE_ETHERNET: 'Ethernet',
            LINK_TYPE_RAW: 'Raw IP',
            LINK_TYPE_LOOP: 'Loopback'
        }
        return names.get(link_type, f'Unknown ({link_type})')
    
    @staticmethod
    def _get_protocol_name(protocol: int) -> str:
        """Get human-readable protocol name"""
        names = {
            IP_PROTO_ICMP: 'ICMP',
            IP_PROTO_TCP: 'TCP',
            IP_PROTO_UDP: 'UDP'
        }
        return names.get(protocol, f'Other ({protocol})')


def analyze_pcap_file(file_data: bytes) -> Dict[str, Any]:
    """Utility function to analyze PCAP file
    
    Args:
        file_data: Raw bytes of PCAP file
        
    Returns:
        Analysis result dictionary
    """
    analyzer = PCAPAnalyzer(file_data)
    return analyzer.parse()
