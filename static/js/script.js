// Confirm deletion of a wine
function confirmDelete(id, name) {
    return confirm(`정말로 "${name}" 와인을 삭제하시겠습니까?`);
}

// Add any other JavaScript functions you might need here
document.addEventListener('DOMContentLoaded', function() {
    console.log('Wine Cellar App Initialized');
    
    // You can add more initialization code here
});

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.delete-link').forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const id = this.getAttribute('data-id');
            const name = this.getAttribute('data-name');
            
            if (confirmDelete(id, name)) {
                window.location.href = `/delete/${id}`;
            }
        });
    });
});