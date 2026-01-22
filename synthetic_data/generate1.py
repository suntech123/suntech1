from sdv.datasets.demo import download_demo
from sdv.single_table import GaussianCopulaSynthesizer

# 1. Get data
real_data, metadata = download_demo(modality='single_table', dataset_name='fake_hotel_guests')

# 2. Create model
synthesizer = GaussianCopulaSynthesizer(metadata)
synthesizer.fit(real_data)

# 3. Generate fake data
print(synthesizer.sample(num_rows=5))
