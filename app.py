.product-info {{
    padding: 20px;
    flex: 1;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #ffffff 0%, #fafafa 100%);
    min-height: 200px;
}}

.product-title {{
    font-size: 17px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    margin: 0 0 12px 0;
    line-height: 1.4;
    min-height: 48px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}

.product-description {{
    font-size: 14px;
    color: {TEXT_SECONDARY};
    line-height: 1.6;
    margin: 0 0 15px 0;
    min-height: 44px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}

.product-price {{
    font-size: 26px;
    font-weight: 800;
    color: {PRICE_COLOR};
    margin: 0 0 12px 0;
    padding: 8px 0;
    display: flex;
    align-items: baseline;
    gap: 5px;
}}

.price-currency {{
    font-size: 16px;
    font-weight: 600;
    color: {TEXT_SECONDARY};
}}
