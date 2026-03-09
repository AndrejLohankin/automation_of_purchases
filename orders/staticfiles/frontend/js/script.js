// Основные функции для frontend

// Получение cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Показ уведомления
function showNotification(message, type) {
    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    notification.style.maxWidth = '500px';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Автоматически закрываем через 3 секунды
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

// Обновление количества товаров в корзине
function updateCartBadge() {
    fetch('/api/v1/basket/')
        .then(response => response.json())
        .then(data => {
            const cartBadge = document.getElementById('cart-badge');
            if (cartBadge) {
                cartBadge.textContent = data.items ? data.items.length : 0;
            }
        })
        .catch(error => {
            console.error('Ошибка при обновлении корзины:', error);
        });
}

// Функция для валидации формы
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Функция для очистки формы
function clearForm(formId) {
    const form = document.getElementById(formId);
    form.reset();
    
    // Удаляем классы валидации
    const inputs = form.querySelectorAll('.is-invalid, .is-valid');
    inputs.forEach(input => {
        input.classList.remove('is-invalid', 'is-valid');
    });
}

// Функция для сериализации формы в JSON
function serializeForm(formId) {
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    const data = {};
    
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    return data;
}

// Функция для показа/скрытия элемента
function toggleElement(elementId, show = true) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = show ? 'block' : 'none';
    }
}

// Функция для показа loader
function showLoader(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="spinner"></div>';
    }
}

// Функция для скрытия loader
function hideLoader(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    }
}

// Функция для форматирования цены
function formatPrice(price) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB'
    }).format(price);
}

// Функция для валидации email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Функция для валидации телефона
function validatePhone(phone) {
    const re = /^[\d\s\-\+\(\)]+$/;
    return re.test(phone) && phone.replace(/\D/g, '').length >= 10;
}

// Функция для показа/скрытия пароля
function togglePassword(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Функция для пагинации
function setupPagination(url, containerId, currentPage = 1) {
    fetch(`${url}?page=${currentPage}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById(containerId);
            if (container) {
                // Очищаем контейнер
                container.innerHTML = '';
                
                // Создаем элементы пагинации
                if (data.previous) {
                    const prevButton = document.createElement('button');
                    prevButton.className = 'btn btn-outline-secondary me-2';
                    prevButton.textContent = 'Предыдущая';
                    prevButton.onclick = () => setupPagination(url, containerId, currentPage - 1);
                    container.appendChild(prevButton);
                }
                
                if (data.next) {
                    const nextButton = document.createElement('button');
                    nextButton.className = 'btn btn-outline-secondary ms-2';
                    nextButton.textContent = 'Следующая';
                    nextButton.onclick = () => setupPagination(url, containerId, currentPage + 1);
                    container.appendChild(nextButton);
                }
            }
        })
        .catch(error => {
            console.error('Ошибка при загрузке пагинации:', error);
        });
}

// Функция для фильтрации данных
function filterData(url, params, containerId, templateFunction) {
    fetch(`${url}?${new URLSearchParams(params).toString()}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById(containerId);
            if (container && templateFunction) {
                container.innerHTML = templateFunction(data);
            }
        })
        .catch(error => {
            console.error('Ошибка при фильтрации данных:', error);
        });
}

// Функция для автодополнения
function setupAutocomplete(inputId, url, onSelect) {
    const input = document.getElementById(inputId);
    let timeout = null;
    let currentRequest = null;
    
    input.addEventListener('input', function() {
        clearTimeout(timeout);
        
        const value = this.value.trim();
        if (value.length < 2) {
            hideAutocomplete();
            return;
        }
        
        timeout = setTimeout(() => {
            if (currentRequest) {
                currentRequest.abort();
            }
            
            const controller = new AbortController();
            currentRequest = controller;
            
            fetch(`${url}?q=${encodeURIComponent(value)}`, { signal: controller.signal })
                .then(response => response.json())
                .then(data => {
                    if (data.length > 0) {
                        showAutocomplete(data, input, onSelect);
                    } else {
                        hideAutocomplete();
                    }
                })
                .catch(error => {
                    if (error.name !== 'AbortError') {
                        console.error('Ошибка при загрузке автодополнения:', error);
                    }
                });
        }, 300);
    });
    
    input.addEventListener('blur', () => {
        setTimeout(hideAutocomplete, 200);
    });
}

// Функция для показа автодополнения
function showAutocomplete(data, input, onSelect) {
    // Создаем контейнер для автодополнения
    let autocompleteContainer = document.getElementById('autocomplete-container');
    if (!autocompleteContainer) {
        autocompleteContainer = document.createElement('div');
        autocompleteContainer.id = 'autocomplete-container';
        autocompleteContainer.className = 'autocomplete-container';
        document.body.appendChild(autocompleteContainer);
    }
    
    // Позиционируем контейнер
    const rect = input.getBoundingClientRect();
    autocompleteContainer.style.left = rect.left + 'px';
    autocompleteContainer.style.top = rect.bottom + 'px';
    autocompleteContainer.style.width = rect.width + 'px';
    
    // Создаем элементы автодополнения
    autocompleteContainer.innerHTML = data.map(item => 
        `<div class="autocomplete-item" data-value="${item.value || item}">${item.label || item}</div>`
    ).join('');
    
    // Добавляем обработчики событий
    const items = autocompleteContainer.querySelectorAll('.autocomplete-item');
    items.forEach(item => {
        item.addEventListener('click', function() {
            input.value = this.textContent;
            if (onSelect) {
                onSelect(this.dataset.value || this.textContent);
            }
            hideAutocomplete();
        });
    });
    
    autocompleteContainer.style.display = 'block';
}

// Функция для скрытия автодополнения
function hideAutocomplete() {
    const autocompleteContainer = document.getElementById('autocomplete-container');
    if (autocompleteContainer) {
        autocompleteContainer.style.display = 'none';
    }
}

// Функция для drag and drop
function setupDragAndDrop(dropzoneId, onDrop) {
    const dropzone = document.getElementById(dropzoneId);
    
    dropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('dropzone-active');
    });
    
    dropzone.addEventListener('dragleave', function() {
        this.classList.remove('dropzone-active');
    });
    
    dropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('dropzone-active');
        
        const files = Array.from(e.dataTransfer.files);
        if (onDrop) {
            onDrop(files);
        }
    });
}

// Функция для чтения файла
function readFile(file, callback) {
    const reader = new FileReader();
    
    reader.onload = function(e) {
        if (callback) {
            callback(e.target.result);
        }
    };
    
    reader.readAsText(file);
}

// Функция для копирования в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Скопировано в буфер обмена', 'success');
    }).catch(err => {
        console.error('Ошибка при копировании:', err);
        showNotification('Не удалось скопировать', 'error');
    });
}

// Функция для печати
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Печать</title>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        .print-only { display: block !important; }
                        .no-print { display: none; }
                    </style>
                </head>
                <body>
                    ${element.innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

// Функция для локализации
function localize(key, locale = 'ru') {
    const translations = {
        ru: {
            'yes': 'Да',
            'no': 'Нет',
            'save': 'Сохранить',
            'cancel': 'Отмена',
            'delete': 'Удалить',
            'edit': 'Редактировать',
            'add': 'Добавить',
            'search': 'Поиск',
            'filter': 'Фильтр',
            'sort': 'Сортировка',
            'loading': 'Загрузка...',
            'error': 'Ошибка',
            'success': 'Успешно'
        }
    };
    
    return translations[locale][key] || key;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const addToCartButtons = document.querySelectorAll('.add-to-cart');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productInfoId = this.dataset.productInfoId;
            const quantity = 1;

            // Создаем CSRF токен
            const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');

            fetch('{% url "add_to_cart" %}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `product_info_id=${productInfoId}&quantity=${quantity}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Обновляем счетчик корзины
                    const cartBadge = document.getElementById('cart-badge');
                    if (cartBadge) {
                        cartBadge.textContent = data.cart_count;
                        cartBadge.style.display = 'inline-block';
                    }
                    showNotification('Товар добавлен в корзину', 'success');
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                showNotification('Ошибка при добавлении товара', 'error');
            });
        });
    });
});

// Добавляем функции в глобальный объект для использования в шаблонах
window.utils = {
    getCookie,
    showNotification,
    updateCartBadge,
    validateForm,
    clearForm,
    serializeForm,
    toggleElement,
    showLoader,
    hideLoader,
    formatPrice,
    validateEmail,
    validatePhone,
    togglePassword,
    setupPagination,
    filterData,
    setupAutocomplete,
    setupDragAndDrop,
    readFile,
    copyToClipboard,
    printElement,
    localize
};