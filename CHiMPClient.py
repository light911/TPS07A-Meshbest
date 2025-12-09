#!/data/program/python/python
"""
測試客戶端程式
使用方式: python test_client.py input_image.jpg [--label]
"""
import sys
import requests
from PIL import Image, ImageDraw, ImageFont
import os
import argparse
import numpy as np
from scipy import ndimage
import logging

def calculate_crystal_center_and_max_diameter(mask_array, x1, y1):
    """
    計算晶體的中心點和最大內接圓直徑

    Args:
        mask_array: 2D numpy array (cropped to box)
        x1, y1: bounding box 左上角座標

    Returns:
        center_x, center_y: 晶體中心在完整圖像中的座標
        max_diameter: 最大內接圓的直徑（不碰到晶體邊緣）
    """
    if mask_array.size == 0:
        return None, None, 0

    # 計算質心（center of mass）
    cy, cx = ndimage.center_of_mass(mask_array)

    # 轉換到完整圖像座標
    center_x = x1 + cx
    center_y = y1 + cy

    # 計算距離變換（distance transform）
    # 每個像素的值表示到最近的背景像素的距離
    distance_map = ndimage.distance_transform_edt(mask_array)

    # 最大距離的2倍就是最大內接圓的直徑
    max_radius = np.max(distance_map)
    max_diameter = max_radius * 2

    return center_x, center_y, max_diameter

def calculate_safe_diameter(center_x, center_y, mask_array, all_masks_info):
    """
    計算從中心點出發，不碰到其他晶體的最大圓形直徑

    Args:
        center_x, center_y: 當前晶體中心座標
        mask_array: 當前晶體的 mask
        x1, y1: 當前晶體 bounding box 左上角座標
        all_masks_info: 所有其他晶體的資訊列表 [(mask, box), ...]

    Returns:
        safe_diameter: 不碰到其他晶體的最大直徑
    """
    # 先計算不碰到自己邊緣的最大直徑
    distance_map = ndimage.distance_transform_edt(mask_array)
    max_radius_self = np.max(distance_map)

    # 計算到其他晶體的最小距離
    min_distance_to_others = float('inf')

    for other_mask, other_box in all_masks_info:
        other_x1, other_y1, other_x2, other_y2 = other_box

        # 檢查是否有可能重疊（簡單的距離預檢查）
        box_distance = max(
            abs(center_x - (other_x1 + other_x2) / 2) - (other_x2 - other_x1) / 2,
            abs(center_y - (other_y1 + other_y2) / 2) - (other_y2 - other_y1) / 2
        )

        if box_distance > max_radius_self * 2:
            continue  # 太遠了，跳過

        # 檢查每個其他晶體的 mask 像素
        for dy in range(len(other_mask)):
            for dx in range(len(other_mask[0])):
                if other_mask[dy][dx] > 0:
                    px = other_x1 + dx
                    py = other_y1 + dy
                    distance = np.sqrt((px - center_x)**2 + (py - center_y)**2)
                    min_distance_to_others = min(min_distance_to_others, distance)

    # 安全直徑是到其他晶體最小距離的2倍（半徑到直徑）
    if min_distance_to_others == float('inf'):
        # 沒有其他晶體，只受自己邊緣限制
        safe_diameter = max_radius_self * 2
    else:
        # 受其他晶體限制
        safe_diameter = min(max_radius_self * 2, min_distance_to_others * 2)

    return safe_diameter

def calculate_iou(box1, box2):
    """
    計算兩個框的 IoU (Intersection over Union)

    Args:
        box1, box2: [x1, y1, x2, y2] 格式的框

    Returns:
        IoU 值 (0-1 之間)
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # 計算交集區域
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    # 如果沒有交集
    if x2_i < x1_i or y2_i < y1_i:
        return 0.0

    # 計算交集面積
    intersection = (x2_i - x1_i) * (y2_i - y1_i)

    # 計算各自的面積
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)

    # 計算聯集面積
    union = area1 + area2 - intersection

    # 計算 IoU
    iou = intersection / union if union > 0 else 0.0

    return iou

def find_overlapping_boxes(predictions, iou_threshold=0.1):
    """
    找出所有重疊的框

    Args:
        predictions: 預測結果列表
        iou_threshold: IoU 閾值，超過此值視為重疊

    Returns:
        重疊框的索引集合
    """
    overlapping_indices = set()
    n = len(predictions)

    for i in range(n):
        for j in range(i + 1, n):
            box1 = predictions[i]['box']
            box2 = predictions[j]['box']

            iou = calculate_iou(box1, box2)

            if iou > iou_threshold:
                overlapping_indices.add(i)
                overlapping_indices.add(j)

    return overlapping_indices
def get_crystal_predict(image_path, server_url="http://localhost:8000",logger:logging.Logger=None,saveimage=True):
    # 檢查檔案是否存在
    if not logger:
        logger = logging.getLogger('get_crystal_predict')
        
    if not os.path.exists(image_path):
        logger.warning(f"錯誤: 找不到圖片檔案 {image_path}")
        return None

    logger.debug(f"正在上傳圖片: {image_path}")

    # 上傳圖片到伺服器
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{server_url}/predict_image",
                files=files,
                timeout=30
            )

        # 檢查回應狀態
        response.raise_for_status()
        result = response.json()

    except requests.exceptions.ConnectionError:
        logger.warning(f"錯誤: 無法連接到伺服器 {server_url}")
        logger.warning("請確認伺服器是否正在運行")
        return None
    except requests.exceptions.Timeout:
        logger.warning("錯誤: 請求超時")
        return None
    except Exception as e:
        logger.warning(f"錯誤: {e}")
        return None
    # 按照信心度排序預測結果（信心度高in front)
    sorted_predictions = sorted(enumerate(result['predictions'], 1), key=lambda x: x[1]['score'],
                                reverse=True)
    if saveimage:
        # 載入原始圖片
        image = Image.open(image_path).convert("RGB")
        # 創建一個透明圖層用於繪製帶透明度的框和遮罩
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        # 用於繪製文字的圖層（不需要透明）
        draw = ImageDraw.Draw(image)
        # 創建一個 numpy 陣列來累積所有遮罩
        mask_overlay = np.zeros((image.size[1], image.size[0], 4), dtype=np.uint8)
        def get_color_for_index(idx, total):
            """為每個實例生成不同的顏色"""
            import colorsys
            # 使用 HSV 色輪，保持飽和度和亮度固定，改變色調
            hue = (idx * 0.618033988749895) % 1.0  # 黃金角度，確保顏色分散
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.95)
            return tuple(int(c * 255) for c in rgb)

        # 按照信心度排序預測結果（信心度低的先繪製，高的後繪製，這樣高信心度的會在上層）
        sorted_predictions_2 = sorted(enumerate(result['predictions'], 1), key=lambda x: x[1]['score'])
        # 先收集所有晶體的中心和安全直徑資訊
        crystal_centers = []
        all_masks_info = []

        # 第一遍：計算所有晶體的中心和內接圓
        for idx, pred in sorted_predictions:
            mask = pred.get('mask', None)
            if mask is not None and len(mask) > 0:
                box = pred['box']
                x1, y1, x2, y2 = [int(coord) for coord in box]
                mask_array = np.array(mask, dtype=np.uint8)

                # 計算中心和內接圓直徑
                center_x, center_y, max_diameter = calculate_crystal_center_and_max_diameter(mask_array, x1, y1)

                if center_x is not None:
                    all_masks_info.append((mask, [x1, y1, x2, y2]))
                    crystal_centers.append({
                        'idx': idx,
                        'center_x': center_x,
                        'center_y': center_y,
                        'inner_diameter': max_diameter,
                        'mask': mask,
                        'box': [x1, y1, x2, y2]
                    })
            # 第三遍：繪製晶體
    for idx, pred in sorted_predictions:
        box = pred['box']  # [x1, y1, x2, y2]
        score = pred['score']
        mask = pred.get('mask', None)  # 2D array (cropped to box)

        x1, y1, x2, y2 = [int(coord) for coord in box]

        # 如果要顯示遮罩且有遮罩數據
        if mask is not None and len(mask) > 0:
            # 為這個實例生成獨特的顏色
            instance_color = get_color_for_index(idx, len(result['predictions']))

            # 將 mask 轉換為 numpy 陣列
            mask_array = np.array(mask, dtype=np.uint8)

            # 確保 mask 尺寸與 box 匹配
            expected_height = y2 - y1
            expected_width = x2 - x1

            if mask_array.shape[0] == expected_height and mask_array.shape[1] == expected_width:
                # 在完整圖像的遮罩層上填充這個實例的顏色
                # alpha 設定為 120 (約 50% 透明度) 以便看到底層圖像
                mask_alpha = int(100 + (score * 100))  # 根據信心度調整透明度 (100-200)

                for dy in range(mask_array.shape[0]):
                    for dx in range(mask_array.shape[1]):
                        if mask_array[dy, dx] > 0:  # 如果這個像素屬於物體
                            py = y1 + dy
                            px = x1 + dx
                            if 0 <= py < mask_overlay.shape[0] and 0 <= px < mask_overlay.shape[1]:
                                # 使用 alpha blending 合併顏色
                                mask_overlay[py, px] = [*instance_color, mask_alpha]
            center_info = next((c for c in crystal_centers if c['idx'] == idx), None)
            if center_info:
                cx, cy = center_info['center_x'], center_info['center_y']
                inner_d = center_info['inner_diameter']
                # safe_d = center_info['safe_diameter']
                safe_d = inner_d
                # 繪製中心點（十字線）
                cross_size = 5
                draw_overlay.line([(cx - cross_size, cy), (cx + cross_size, cy)], fill=(255, 255, 0, 255), width=2)
                draw_overlay.line([(cx, cy - cross_size), (cx, cy + cross_size)], fill=(255, 255, 0, 255), width=2)
            # 繪製安全圓（不碰到其他晶體的最大圓，青色虛線）
                safe_r = safe_d / 2
                draw_overlay.ellipse(
                    [cx - safe_r, cy - safe_r, cx + safe_r, cy + safe_r],
                    outline=(0, 255, 255, 180), width=2
                )
            # 將透明圖層合併到原始圖片上
    image = image.convert("RGBA")

    # 如果有遮罩，先合併遮罩層
    mask_image = Image.fromarray(mask_overlay, mode='RGBA')
    image = Image.alpha_composite(image, mask_image)
    image = image.convert("RGB")
    # 生成輸出檔案名稱
    base_name = os.path.splitext(image_path)[0]
    suffix = "_masks" 
    output_path = f"{base_name}{suffix}.jpg"

    # 儲存標註後的圖片
    image.save(output_path, quality=95)




    return sorted_predictions



def test_predict_image(image_path, server_url="http://localhost:8000", show_labels=False, mark_overlaps=False, confidence_threshold=None, show_masks=False, show_centers=False, show_boxes=True):
    """
    上傳圖片到伺服器進行預測，並將結果標註在圖片上

    Args:
        image_path: 輸入圖片路徑
        server_url: 伺服器 URL
        show_labels: 是否顯示標籤
        mark_overlaps: 是否將重疊的框標記為紅色
        confidence_threshold: 信心度閾值，只顯示大於此值的結果 (None = 不篩選)
        show_masks: 是否顯示實例分割遮罩（半透明彩色填充）
        show_centers: 是否顯示晶體中心點和最大內接圓
        show_boxes: 是否顯示邊界框（預設: True）
    """
    # 檢查檔案是否存在
    if not os.path.exists(image_path):
        print(f"錯誤: 找不到圖片檔案 {image_path}")
        sys.exit(1)

    print(f"正在上傳圖片: {image_path}")

    # 上傳圖片到伺服器
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{server_url}/predict_image",
                files=files,
                timeout=30
            )

        # 檢查回應狀態
        response.raise_for_status()
        result = response.json()

    except requests.exceptions.ConnectionError:
        print(f"錯誤: 無法連接到伺服器 {server_url}")
        print("請確認伺服器是否正在運行")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("錯誤: 請求超時")
        sys.exit(1)
    except Exception as e:
        print(f"錯誤: {e}")
        sys.exit(1)

    # 顯示預測結果
    print(f"\n預測結果:")
    print(f"狀態: {result['status']}")
    print(f"晶體數量: {result['crystal_count']}")
    print(f"找到 {len(result['predictions'])} 個晶體\n")

    # 如果設定了信心度閾值，進行篩選
    if confidence_threshold is not None:
        original_count = len(result['predictions'])
        result['predictions'] = [pred for pred in result['predictions'] if pred['score'] >= confidence_threshold]
        filtered_count = len(result['predictions'])
        print(f"📊 信心度篩選 (>= {confidence_threshold}): {original_count} → {filtered_count} 個晶體\n")

    # 如果啟用重疊檢測，找出重疊的框
    overlapping_indices = set()
    if mark_overlaps:
        overlapping_indices = find_overlapping_boxes(result['predictions'])
        if overlapping_indices:
            print(f"⚠ 找到 {len(overlapping_indices)} 個重疊的框，將標記為紅色\n")

    # 載入原始圖片
    image = Image.open(image_path).convert("RGB")
    # 創建一個透明圖層用於繪製帶透明度的框和遮罩
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    # 用於繪製文字的圖層（不需要透明）
    draw = ImageDraw.Draw(image)

    # 如果要顯示遮罩，創建一個 numpy 陣列來累積所有遮罩
    if show_masks:
        mask_overlay = np.zeros((image.size[1], image.size[0], 4), dtype=np.uint8)

    # 嘗試載入字體，如果失敗則使用預設字體
    try:
        # 使用較大的字體以便清楚顯示
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        try:
            # 嘗試其他常見字體路徑
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            # 使用預設字體
            font = ImageFont.load_default()

    # 定義一組視覺上容易區分的顏色（HSV 色輪均勻分布）
    def get_color_for_index(idx, total):
        """為每個實例生成不同的顏色"""
        import colorsys
        # 使用 HSV 色輪，保持飽和度和亮度固定，改變色調
        hue = (idx * 0.618033988749895) % 1.0  # 黃金角度，確保顏色分散
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.95)
        return tuple(int(c * 255) for c in rgb)

    # 按照信心度排序預測結果（信心度低的先繪製，高的後繪製，這樣高信心度的會在上層）
    sorted_predictions = sorted(enumerate(result['predictions'], 1), key=lambda x: x[1]['score'])

    # 先收集所有晶體的中心和安全直徑資訊
    crystal_centers = []
    all_masks_info = []

    # 第一遍：計算所有晶體的中心和內接圓
    for idx, pred in sorted_predictions:
        mask = pred.get('mask', None)
        if mask is not None and len(mask) > 0:
            box = pred['box']
            x1, y1, x2, y2 = [int(coord) for coord in box]
            mask_array = np.array(mask, dtype=np.uint8)

            # 計算中心和內接圓直徑
            center_x, center_y, max_diameter = calculate_crystal_center_and_max_diameter(mask_array, x1, y1)

            if center_x is not None:
                all_masks_info.append((mask, [x1, y1, x2, y2]))
                crystal_centers.append({
                    'idx': idx,
                    'center_x': center_x,
                    'center_y': center_y,
                    'inner_diameter': max_diameter,
                    'mask': mask,
                    'box': [x1, y1, x2, y2]
                })

    # 第二遍：計算安全直徑（不碰到其他晶體）
    for info in crystal_centers:
        # 排除自己
        other_masks = [(m, b) for m, b in all_masks_info if b != info['box']]
        safe_diameter = calculate_safe_diameter(
            info['center_x'], info['center_y'],
            np.array(info['mask'], dtype=np.uint8),
            other_masks
        )
        info['safe_diameter'] = safe_diameter

    # 第三遍：繪製晶體
    for idx, pred in sorted_predictions:
        box = pred['box']  # [x1, y1, x2, y2]
        score = pred['score']
        mask = pred.get('mask', None)  # 2D array (cropped to box)

        x1, y1, x2, y2 = [int(coord) for coord in box]

        # 根據信心度計算透明度 (信心度越高，越不透明)
        # score 範圍 0-1，alpha 範圍 0-255
        # 設定最小透明度為 50 (避免完全看不見)，最大為 255 (完全不透明)
        alpha = int(50 + (score * 205))  # 50 + score * (255-50)

        # 判斷此框是否重疊，決定顏色
        is_overlapping = (idx - 1) in overlapping_indices
        if is_overlapping:
            # 重疊的框使用紅色
            box_color = (255, 0, 0)
        else:
            # 正常框使用綠色
            box_color = (0, 255, 0)

        color_with_alpha = (*box_color, alpha)

        # 如果要顯示遮罩且有遮罩數據
        if show_masks and mask is not None and len(mask) > 0:
            # 為這個實例生成獨特的顏色
            instance_color = get_color_for_index(idx, len(result['predictions']))

            # 將 mask 轉換為 numpy 陣列
            mask_array = np.array(mask, dtype=np.uint8)

            # 確保 mask 尺寸與 box 匹配
            expected_height = y2 - y1
            expected_width = x2 - x1

            if mask_array.shape[0] == expected_height and mask_array.shape[1] == expected_width:
                # 在完整圖像的遮罩層上填充這個實例的顏色
                # alpha 設定為 120 (約 50% 透明度) 以便看到底層圖像
                mask_alpha = int(100 + (score * 100))  # 根據信心度調整透明度 (100-200)

                for dy in range(mask_array.shape[0]):
                    for dx in range(mask_array.shape[1]):
                        if mask_array[dy, dx] > 0:  # 如果這個像素屬於物體
                            py = y1 + dy
                            px = x1 + dx
                            if 0 <= py < mask_overlay.shape[0] and 0 <= px < mask_overlay.shape[1]:
                                # 使用 alpha blending 合併顏色
                                mask_overlay[py, px] = [*instance_color, mask_alpha]

        # 畫矩形框 (帶透明度，線寬3)
        if show_boxes:
            draw_overlay.rectangle([x1, y1, x2, y2], outline=color_with_alpha, width=3)

        # 如果啟用標籤，則顯示編號和信心度
        if show_labels:
            # 準備標籤文字
            label = f"#{idx} ({score:.2f})"

            # 獲取文字邊界框
            bbox = draw.textbbox((x1, y1), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 畫背景矩形讓文字更清楚 (使用相同顏色和透明度)
            draw_overlay.rectangle(
                [x1, y1 - text_height - 4, x1 + text_width + 4, y1],
                fill=color_with_alpha
            )

            # 畫文字 (白色，不透明)
            draw_overlay.text((x1 + 2, y1 - text_height - 2), label, fill=(255, 255, 255, 255), font=font)

        # 繪製中心點和圓圈
        if show_centers:
            # 找到對應的中心資訊
            center_info = next((c for c in crystal_centers if c['idx'] == idx), None)
            if center_info:
                cx, cy = center_info['center_x'], center_info['center_y']
                inner_d = center_info['inner_diameter']
                safe_d = center_info['safe_diameter']

                # 繪製中心點（十字線）
                cross_size = 5
                draw_overlay.line([(cx - cross_size, cy), (cx + cross_size, cy)], fill=(255, 255, 0, 255), width=2)
                draw_overlay.line([(cx, cy - cross_size), (cx, cy + cross_size)], fill=(255, 255, 0, 255), width=2)

                # 繪製內接圓（晶體本身的最大圓，黃色虛線）
                # inner_r = inner_d / 2
                # draw_overlay.ellipse(
                #     [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
                #     outline=(255, 255, 0, 180), width=2
                # )

                # 繪製安全圓（不碰到其他晶體的最大圓，青色虛線）
                safe_r = safe_d / 2
                draw_overlay.ellipse(
                    [cx - safe_r, cy - safe_r, cx + safe_r, cy + safe_r],
                    outline=(0, 255, 255, 180), width=2
                )

        # 顯示框的資訊，如果是重疊的框會加上標記
        overlap_mark = " [重疊]" if is_overlapping else ""
        mask_info = f", 遮罩大小: {len(mask)}x{len(mask[0]) if mask and len(mask) > 0 else 0}" if show_masks and mask else ""

        # 添加中心點資訊
        center_info_text = ""
        if show_centers:
            center_info = next((c for c in crystal_centers if c['idx'] == idx), None)
            if center_info:
                center_info_text = f", 中心: ({center_info['center_x']:.1f}, {center_info['center_y']:.1f}), 內接圓直徑: {center_info['inner_diameter']:.1f}px, 安全直徑: {center_info['safe_diameter']:.1f}px"

        print(f"晶體 #{idx}: 位置 [{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}], 信心度: {score:.3f}{overlap_mark}{mask_info}{center_info_text}")

    # 將透明圖層合併到原始圖片上
    image = image.convert("RGBA")

    # 如果有遮罩，先合併遮罩層
    if show_masks:
        mask_image = Image.fromarray(mask_overlay, mode='RGBA')
        image = Image.alpha_composite(image, mask_image)

    # 再合併框和標籤
    image = Image.alpha_composite(image, overlay)
    image = image.convert("RGB")

    # 生成輸出檔案名稱
    base_name = os.path.splitext(image_path)[0]
    suffix = "_annotated_masks" if show_masks else "_annotated"
    output_path = f"{base_name}{suffix}.jpg"

    # 儲存標註後的圖片
    image.save(output_path, quality=95)
    print(f"\n✓ 已將標註結果儲存至: {output_path}")

    return result

def main():
    parser = argparse.ArgumentParser(
        description='測試晶體檢測 API 並標註結果圖片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例:
  python test_client.py test.jpg
  python test_client.py test.jpg --label
  python test_client.py test.jpg --overlap
  python test_client.py test.jpg --mask
  python test_client.py test.jpg --mask --label
  python test_client.py test.jpg --confidence 0.3
  python test_client.py test.jpg --confidence 0.5 --label
  python test_client.py test.jpg --label --overlap --confidence 0.3
  python test_client.py test.jpg --mask --label --confidence 0.3
  python test_client.py test.jpg --mask --center --label
  python test_client.py test.jpg --center
  python test_client.py test.jpg --mask --no-box
  python test_client.py test.jpg --mask --center --no-box --label
  python test_client.py test.jpg --server http://192.168.1.100:8000
  python test_client.py test.jpg --label --overlap --confidence 0.3 --server http://192.168.1.100:8000
        '''
    )

    parser.add_argument('image_path', help='輸入圖片路徑')
    parser.add_argument('--server', default='http://localhost:8000',
                        help='伺服器 URL (預設: http://localhost:8000)')
    parser.add_argument('--label', action='store_true',
                        help='在圖片上顯示編號和信心度標籤')
    parser.add_argument('--overlap', action='store_true',
                        help='將重疊的框標記為紅色')
    parser.add_argument('--confidence', type=float, default=None,
                        help='信心度閾值，只顯示大於等於此值的結果 (0.0-1.0，預設: 不篩選。建議值: 0.3)')
    parser.add_argument('--mask', action='store_true',
                        help='顯示實例分割遮罩（用半透明彩色填充顯示每個晶體的精確形狀）')
    parser.add_argument('--center', action='store_true',
                        help='顯示晶體中心點和最大內接圓（黃色）及安全圓（青色，不碰到其他晶體）')
    parser.add_argument('--no-box', dest='show_box', action='store_false', default=True,
                        help='不顯示邊界框（預設會顯示）')

    args = parser.parse_args()

    test_predict_image(args.image_path, args.server, args.label, args.overlap, args.confidence, args.mask, args.center, args.show_box)

if __name__ == "__main__":
    main()
