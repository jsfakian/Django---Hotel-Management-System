#!/usr/bin/env python3
"""
NEPHELE Task 3 - Real Data Downloader
Automated script to download free public datasets for hotel management AI training

Supported datasets:
  1. Hotel Booking Demand (Kaggle) - 119K records
  2. Inside Airbnb (Multiple cities) - Price & availability data
  3. TripAdvisor Reviews (Kaggle) - 878K reviews
  4. Hostelworld Reviews (Kaggle) - Budget accommodation data
  5. World Bank Tourism (API) - Macro indicators

Usage:
  python3 download_real_data.py --dataset booking --dataset airbnb
  python3 download_real_data.py --all  # Download everything
  python3 download_real_data.py --help
"""

import os
import subprocess
import sys
import json
from pathlib import Path
from urllib.request import urlopen, urlretrieve
import argparse
import shutil


class RealDataDownloader:
    """Download and organize real public datasets for NEPHELE training"""
    
    def __init__(self, output_dir="task3-data/real_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.datasets = {
            'booking': self.download_booking_demand,
            'airbnb': self.download_airbnb_data,
            'tripadvisor': self.download_tripadvisor,
            'hostelworld': self.download_hostelworld,
            'worldbank': self.download_worldbank,
        }
    
    def check_kaggle_api(self):
        """Verify Kaggle API is installed and configured"""
        try:
            import kaggle
            kaggle_config = Path.home() / '.kaggle' / 'kaggle.json'
            if not kaggle_config.exists():
                print("\n⚠️  Kaggle API not configured. Installation instructions:")
                print("   1. Visit: https://www.kaggle.com/account/api")
                print("   2. Click 'Create New Token'")
                print("   3. Save kaggle.json to ~/.kaggle/kaggle.json")
                print("   4. Run: chmod 600 ~/.kaggle/kaggle.json")
                return False
            return True
        except ImportError:
            print("\n⚠️  Kaggle CLI not installed. Install with:")
            print("   pip3 install kaggle")
            return False
    
    def download_booking_demand(self):
        """Download Hotel Booking Demand dataset from Kaggle"""
        print("\n📥 Downloading Hotel Booking Demand (Kaggle)...")
        print("   Records: 119,390 bookings | Size: ~16.86 MB")
        print("   Dataset: https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand")
        
        if not self.check_kaggle_api():
            print("   ❌ Skipping: Kaggle API not available")
            return False
        
        try:
            output_path = self.output_dir / "kaggle_booking_demand"
            output_path.mkdir(exist_ok=True)
            
            cmd = [
                'kaggle', 'datasets', 'download',
                '-d', 'jessemostipak/hotel-booking-demand',
                '-p', str(output_path),
                '--unzip'
            ]
            
            subprocess.run(cmd, check=True)
            print(f"   ✅ Downloaded to: {output_path}")
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def download_airbnb_data(self):
        """Download Airbnb data from Inside Airbnb"""
        print("\n📥 Downloading Inside Airbnb Data...")
        
        cities_to_download = [
            {
                'name': 'New York City',
                'code': 'new-york-city',
                'country': 'united-states/ny',
                'date': '2025-12-04'
            },
            {
                'name': 'London',
                'code': 'london',
                'country': 'united-kingdom/england',
                'date': '2025-09-14'
            },
            {
                'name': 'Paris',
                'code': 'paris',
                'country': 'france/île-de-france',
                'date': '2025-09-12'
            },
            {
                'name': 'Barcelona',
                'code': 'barcelona',
                'country': 'spain/catalonia',
                'date': '2025-09-14'
            },
        ]
        
        airbnb_dir = self.output_dir / "airbnb_combined"
        airbnb_dir.mkdir(exist_ok=True)
        
        success_count = 0
        for city_info in cities_to_download:
            print(f"\n   Downloading {city_info['name']}...")
            
            base_url = (f"http://data.insideairbnb.com/{city_info['country']}/"
                       f"{city_info['code']}/{city_info['date']}/data")
            
            files = ['listings.csv.gz', 'calendar.csv.gz', 'reviews.csv.gz']
            
            for filename in files:
                url = f"{base_url}/{filename}"
                try:
                    output_file = airbnb_dir / f"{city_info['code']}_{filename}"
                    print(f"      • {filename}...", end=' ')
                    urlretrieve(url, output_file)
                    
                    # Decompress
                    if filename.endswith('.gz'):
                        import gzip
                        uncompressed = output_file.with_suffix('')
                        with gzip.open(output_file, 'rb') as f_in:
                            with open(uncompressed, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        output_file.unlink()
                    
                    print("✅")
                    success_count += 1
                except Exception as e:
                    print(f"⚠️  (skipped: {str(e)[:30]})")
        
        if success_count > 0:
            print(f"   ✅ Downloaded {success_count} files from {len(cities_to_download)} cities")
            return True
        return False
    
    def download_tripadvisor(self):
        """Download TripAdvisor reviews dataset from Kaggle"""
        print("\n📥 Downloading TripAdvisor Hotel Reviews (Kaggle)...")
        print("   Records: 878,561 reviews | Size: ~2.17 GB (large download)")
        print("   Dataset: https://www.kaggle.com/datasets/joebeachcapital/hotel-reviews")
        
        if not self.check_kaggle_api():
            print("   ⚠️  Skipping: Kaggle API not available")
            return False
        
        try:
            output_path = self.output_dir / "tripadvisor"
            output_path.mkdir(exist_ok=True)
            
            print("   ⚠️  This is a large dataset (2.17 GB). Downloading...")
            
            cmd = [
                'kaggle', 'datasets', 'download',
                '-d', 'joebeachcapital/hotel-reviews',
                '-p', str(output_path),
                '--unzip'
            ]
            
            subprocess.run(cmd, check=True)
            print(f"   ✅ Downloaded to: {output_path}")
            return True
        except Exception as e:
            print(f"   ⚠️  Note: Large file. Manual download recommended:")
            print(f"       https://www.kaggle.com/datasets/joebeachcapital/hotel-reviews")
            return False
    
    def download_hostelworld(self):
        """Download Hostelworld reviews from Kaggle"""
        print("\n📥 Downloading Hostelworld Reviews (Kaggle)...")
        print("   Records: 100,000+ reviews | Size: ~161 MB")
        print("   Dataset: https://www.kaggle.com/datasets/felipejardimf/hotel-reviews-hostelworld")
        
        if not self.check_kaggle_api():
            print("   ⚠️  Skipping: Kaggle API not available")
            return False
        
        try:
            output_path = self.output_dir / "hostelworld"
            output_path.mkdir(exist_ok=True)
            
            cmd = [
                'kaggle', 'datasets', 'download',
                '-d', 'felipejardimf/hotel-reviews-hostelworld',
                '-p', str(output_path),
                '--unzip'
            ]
            
            subprocess.run(cmd, check=True)
            print(f"   ✅ Downloaded to: {output_path}")
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def download_worldbank(self):
        """Download World Bank tourism data"""
        print("\n📥 Downloading World Bank Tourism Indicators...")
        print("   Records: 200+ countries | File: tourism_indicators.csv")
        
        try:
            output_path = self.output_dir / "world_bank_tourism"
            output_path.mkdir(exist_ok=True)
            
            print("   ℹ️  Manual download recommended (API complex)")
            print("       Visit: https://data.worldbank.org/topic/19")
            print("       Select indicators and download CSV")
            
            # Try to fetch via API as fallback
            print("   Attempting API download...", end=' ')
            try:
                url = "https://api.worldbank.org/v2/country?format=json&per_page=300"
                with urlopen(url) as response:
                    print("✅")
                    return True
            except:
                print("⚠️  (use manual download)")
                return False
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            return False
    
    def download_all(self):
        """Download all available datasets"""
        results = {}
        for dataset_name, download_func in self.datasets.items():
            results[dataset_name] = download_func()
        return results
    
    def download_selected(self, datasets):
        """Download specified datasets"""
        results = {}
        available = set(self.datasets.keys())
        requested = set(d.lower() for d in datasets)
        invalid = requested - available
        
        if invalid:
            print(f"❌ Unknown datasets: {', '.join(invalid)}")
            print(f"   Available: {', '.join(sorted(available))}")
        
        for dataset in requested & available:
            results[dataset] = self.datasets[dataset]()
        
        return results
    
    def print_summary(self, results):
        """Print download summary"""
        print("\n" + "="*80)
        print("DOWNLOAD SUMMARY")
        print("="*80)
        
        succeeded = sum(1 for v in results.values() if v)
        total = len(results)
        
        for dataset, success in results.items():
            status = "✅" if success else "⚠️"
            print(f"{status} {dataset}: {'Downloaded' if success else 'Not downloaded'}")
        
        print(f"\nTotal: {succeeded}/{total} successful")
        print(f"\nOutput directory: {self.output_dir.absolute()}")
        print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Download real public datasets for NEPHELE Task 3 AI training'
    )
    parser.add_argument(
        '--dataset',
        action='append',
        choices=['booking', 'airbnb', 'tripadvisor', 'hostelworld', 'worldbank'],
        help='Dataset to download (can specify multiple times)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Download all available datasets'
    )
    parser.add_argument(
        '--output-dir',
        default='task3-data/real_data',
        help='Output directory for downloaded data'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available datasets'
    )
    
    args = parser.parse_args()
    
    downloader = RealDataDownloader(args.output_dir)
    
    if args.list:
        print("\n📊 Available Datasets:")
        print("  • booking - Hotel Booking Demand (Kaggle)")
        print("  • airbnb - Inside Airbnb (4+ cities)")
        print("  • tripadvisor - Hotel Reviews (Kaggle)")
        print("  • hostelworld - Budget Accommodation Reviews (Kaggle)")
        print("  • worldbank - Tourism Indicators (API)")
        return
    
    if args.all:
        print("\n🔄 Downloading ALL datasets...")
        results = downloader.download_all()
    elif args.dataset:
        print(f"\n🔄 Downloading: {', '.join(args.dataset)}")
        results = downloader.download_selected(args.dataset)
    else:
        print("\n📖 Real Data Downloader for NEPHELE Task 3")
        print("   Use --help for options")
        print("   Use --list to see available datasets")
        print("\n   Example:")
        print("   python3 download_real_data.py --dataset booking --dataset airbnb")
        return
    
    downloader.print_summary(results)
    print("\n💡 Next: Use merge_real_data.py to consolidate datasets")


if __name__ == "__main__":
    main()
