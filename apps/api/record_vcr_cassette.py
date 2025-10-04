#!/usr/bin/env python3
# ABOUTME: Script to create VCR cassette for NASA POWER API testing
# ABOUTME: Records a real API call for offline testing replay

import asyncio
from datetime import date
from pathlib import Path
import vcr
from app.weather.power import PowerClient

async def record_power_api_call():
    """Record a NASA POWER API call for testing."""
    
    cassette_path = Path(__file__).parent / "tests" / "cassettes" / "power_api_fortaleza_sample.yaml"
    
    # Configure VCR
    my_vcr = vcr.VCR(
        serializer="yaml",
        record_mode="new_episodes",
        decode_compressed_response=True
    )
    
    with my_vcr.use_cassette(str(cassette_path)):
        client = PowerClient()
        
        try:
            # Record API call for Fortaleza  
            data = await client.get_daily_data(
                latitude=-3.7275,
                longitude=-38.5275, 
                start_date=date(2023, 6, 1),
                end_date=date(2023, 6, 7)
            )
            
            print(f"✅ Successfully recorded full API call")
            print(f"📊 Parameters: {list(data['properties']['parameter'].keys())}")
            print(f"📅 Date range: {len(data['properties']['parameter']['T2M'])} days")
            
            # Also record custom parameters call
            cassette_path_2 = Path(__file__).parent / "tests" / "cassettes" / "power_api_custom_params.yaml"
            
            with my_vcr.use_cassette(str(cassette_path_2)):
                # Record API call with custom parameters
                data2 = await client.get_daily_data(
                    latitude=-3.7275,
                    longitude=-38.5275,
                    start_date=date(2023, 6, 1),
                    end_date=date(2023, 6, 2),
                    parameters=["T2M", "RH2M"]
                )
                
                print(f"✅ Successfully recorded custom params API call")
                print(f"📊 Custom parameters: {list(data2['properties']['parameter'].keys())}")
                print(f"📅 Date range: {len(data2['properties']['parameter']['T2M'])} days")
            
        except Exception as e:
            print(f"❌ Failed to record API call: {e}")
        finally:
            await client.close()

if __name__ == "__main__":
    asyncio.run(record_power_api_call())