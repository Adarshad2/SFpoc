
import os
def setup_project():
    os.makedirs('data/images', exist_ok=True)
    print('Created data/images folder. Please add product images into data/images if you want to replace defaults.')
if __name__ == '__main__':
    setup_project()
