let selectedShelf = null;

function selectShelf(shelfNumber) {
    // 이전 선택 해제
    if (selectedShelf) {
        document.querySelector(`.shelf-${selectedShelf}`).classList.remove('selected');
    }
    
    // 새로운 선반 선택
    selectedShelf = shelfNumber;
    document.querySelector(`.shelf-${shelfNumber}`).classList.add('selected');
    
    // 셀러 이미지 컴팩트 모드로 전환
    document.getElementById('cellarContainer').classList.add('compact');
    
    // 선반 상세 패널 표시
    showShelfDetail(shelfNumber);
}

function showShelfDetail(shelfNumber) {
    const detailPanel = document.getElementById('shelfDetail');
    const shelfTitle = document.getElementById('shelfTitle');
    const shelfWines = document.getElementById('shelfWines');
    
    // 제목 업데이트
    shelfTitle.textContent = `선반 ${shelfNumber}`;
    
    // 로딩 표시
    shelfWines.innerHTML = '<div class="loading">로딩 중...</div>';
    
    // 패널 표시
    detailPanel.style.display = 'block';
    
    // AJAX로 해당 선반의 와인 목록 가져오기
    fetch(`/api/shelf/${shelfNumber}/wines`)
        .then(response => response.json())
        .then(wines => {
            displayShelfWines(wines, shelfNumber);
        })
        .catch(error => {
            console.error('Error:', error);
            shelfWines.innerHTML = '<div class="error">데이터를 불러오는 중 오류가 발생했습니다.</div>';
        });
}

function displayShelfWines(wines, shelfNumber) {
    const shelfWines = document.getElementById('shelfWines');
    
    if (wines.length === 0) {
        // 로그인 상태에 따라 다른 메시지 표시
        const isLoggedIn = document.querySelector('.user-info') !== null;
        const addButton = isLoggedIn ? '<a href="/add" class="add-button">와인 추가하기</a>' : '';
        
        shelfWines.innerHTML = `
            <div class="empty-shelf">
                <p>이 선반은 비어있습니다.</p>
                ${addButton}
            </div>
        `;
        return;
    }
    
    let html = '';
    const isLoggedIn = document.querySelector('.user-info') !== null;
    
    wines.forEach(wine => {
        // 수정/삭제 버튼은 로그인한 경우만 표시
        const actionButtons = isLoggedIn ? `
            <div class="actions">
                <a href="/edit/${wine.id}" class="edit-link">수정</a>
                <a href="#" onclick="deleteWine(${wine.id})" class="delete-link">삭제</a>
            </div>
        ` : '';
        
        const wineType = wine.type;
        let wineCardClass = 'shelf-wine-card';
        if (wineType === 1) wineCardClass = 'shelf-wine-card-red';
        else if (wineType === 2) wineCardClass = 'shelf-wine-card-white';
        else if (wineType === 3) wineCardClass = 'shelf-wine-card-sparkling';

        html += `
            <div class="${wineCardClass}">
                ${wine.position ? `<div class="position-badge">위치 ${wine.position}</div>` : ''}
                <div class="wine-name">${wine.name}</div>
                <div class="wine-info">
                    <span class="info-label">국가:</span> ${wine.country || 'N/A'} | 
                    <span class="info-label">지역:</span> ${wine.region || 'N/A'}
                </div>
                <div class="wine-info">
                    <span class="info-label">연도:</span> ${wine.year || 'N/A'} | 
                    <span class="info-label">품종:</span> ${wine.grape_variety || 'N/A'}
                </div>
                ${wine.price ? `<div class="wine-price">${parseInt(wine.price).toLocaleString()}원</div>` : ''}
                ${wine.notes ? `<div class="wine-note">"${wine.notes}"</div>` : ''}
                ${actionButtons}
            </div>
        `;
    });
    
    shelfWines.innerHTML = html;
}

function closeShelfDetail() {
    // 선택 해제
    if (selectedShelf) {
        document.querySelector(`.shelf-${selectedShelf}`).classList.remove('selected');
        selectedShelf = null;
    }
    
    // 셀러 이미지 원래 크기로 복원
    document.getElementById('cellarContainer').classList.remove('compact');
    
    // 상세 패널 숨기기
    document.getElementById('shelfDetail').style.display = 'none';
}

function deleteWine(wineId) {
    if (confirm('정말로 이 와인을 삭제하시겠습니까?')) {
        fetch(`/delete/${wineId}`, {
            method: 'POST',
        })
        .then(response => {
            if (response.ok) {
                // 현재 선반 새로고침
                if (selectedShelf) {
                    showShelfDetail(selectedShelf);
                }
                // 선반 카운트 업데이트
                updateShelfCounts();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('삭제 중 오류가 발생했습니다.');
        });
    }
}

function updateShelfCounts() {
    fetch('/api/cellar/overview')
        .then(response => response.json())
        .then(cellarData => {
            cellarData.forEach(shelf => {
                const countElement = document.querySelector(`.shelf-${shelf.shelf_number} .shelf-count`);
                if (countElement) {
                    countElement.innerHTML = `
                        <span class="count">${shelf.wine_count}</span>
                        <span class="capacity">/${shelf.max_capacity}</span>
                    `;
                }
            });
        });
}

// 키보드 단축키
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && selectedShelf) {
        closeShelfDetail();
    }
});

// 모바일에서 터치 이벤트 최적화
if ('ontouchstart' in window) {
    document.querySelectorAll('.shelf-indicator').forEach(shelf => {
        shelf.addEventListener('touchstart', function(e) {
            e.preventDefault();
            this.click();
        });
    });
}