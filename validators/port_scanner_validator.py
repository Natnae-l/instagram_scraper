import ipaddress
from pydantic import BaseModel, Field, model_validator


class PortRange(BaseModel):
    start_port: int = Field(..., ge=0, le=65535,
                            description="Start of the port range")
    end_port: int = Field(..., ge=0, le=65535,
                          description="End of the port range")
    ip_address: str

    @model_validator(mode='after')
    def check_port_order(self) -> 'PortRange':
        if self.start_port > self.end_port:
            raise ValueError(
                "start_port must be less than or equal to end_port"
            )
        if self.end_port - self.start_port > 4:
            raise ValueError(
                'maximum number of port to scan is 4, please rearrange your port numbers for a good fit')
        return self

    @model_validator(mode='after')
    def validate_ip(self) -> 'PortRange':
        try:
            ipaddress.ip_address(self.ip_address)
        except ValueError as e:
            raise ValueError(f"Invalid IP address: {str(e)}")
        return self
