# -*- coding: utf-8 -*-
import re
from urllib.parse import urlparse, urlunparse, parse_qs

def normalize_url(url, target_pattern):
    """
    Normaliza una URL eliminando parámetros de consulta innecesarios
    """
    if not url:
        return url
    
    try:
        parsed_url = urlparse(url)
        
        # Eliminar fragmentos (#)
        normalized_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            '',  # query vacío
            ''   # fragment vacío
        ))
        
        # Asegurar que termine con /
        if not normalized_url.endswith('/') and not parsed_url.path.endswith('.html'):
            normalized_url += '/'
            
        return normalized_url
        
    except Exception:
        return url

def is_target_url(url, target_pattern, excluded_endings, excluded_patterns):
    """
    Determina si una URL es objetivo para ser guardada
    """
    if not url or not target_pattern:
        return False
    
    # Debe contener el patrón objetivo
    if target_pattern not in url:
        return False
    
    # No debe terminar con patrones excluidos
    if excluded_endings:
        for ending in excluded_endings:
            if url.rstrip('/').endswith(ending):
                return False
    
    # No debe contener patrones excluidos
    if excluded_patterns:
        for pattern in excluded_patterns:
            if pattern in url:
                return False
    
    return True

def is_no_visit(url, target_pattern, excluded_patterns):
    """
    Determina si una URL NO debe ser visitada
    """
    if not url:
        return True
    
    # URLs que no pertenecen al dominio objetivo
    if 'idealista.com' not in url:
        return True
    
    # URLs que no contienen el patrón objetivo (TARGET_URL_PATTERN)
    # Solo crawlear URLs que contengan el patrón objetivo
    if target_pattern and target_pattern not in url:
        return True
    
    # URLs con patrones excluidos
    if excluded_patterns:
        for pattern in excluded_patterns:
            if pattern in url:
                return True
    
    # URLs de JavaScript, CSS, imágenes, etc.
    file_extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.pdf']
    for ext in file_extensions:
        if url.lower().endswith(ext):
            return True
    
    return False