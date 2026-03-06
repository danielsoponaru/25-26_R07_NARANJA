def preprocesar_datos(X_train, X_val, y_train, reduccion_config, encoding_type):
    """
    Preprocesa los datos según configuración especificada.
    
    Pasos:
    1. Encoding de categóricas (OHE o Target)
    2. Estandarización
    3. PCA (opcional)
    
    Retorna:
    --------
    X_train_processed, X_val_processed, scaler, pca (si aplica)
    """
    X_train_proc = X_train.copy()
    X_val_proc = X_val.copy()
    
    # PASO 1: ENCODING
    if encoding_type == 'one_hot':
        # One-Hot Encoding (las categóricas ya están en formato 0/1, no hacer nada)
        pass
    
    elif encoding_type == 'target_encoding':
        # Target encoding regularizado
        if len(categorical_features) > 0:
            X_train_proc, X_val_proc, _ = target_encoding_regularizado(
                X_train_proc, y_train, X_val_proc, categorical_features, m=10
            )
    
    # PASO 2: ESTANDARIZACIÓN
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_proc)
    X_val_scaled = scaler.transform(X_val_proc)
    
    # PASO 3: PCA (opcional)
    pca = None
    if reduccion_config['use_pca']:
        n_comp = reduccion_config['n_components']
        pca = PCA(n_components=n_comp, random_state=42)
        X_train_scaled = pca.fit_transform(X_train_scaled)
        X_val_scaled = pca.transform(X_val_scaled)
    
    return X_train_scaled, X_val_scaled, scaler, pca

def evaluar_modelo(y_true, y_pred, conjunto_nombre=''):
    """
    Calcula métricas de regresión.
    
    Retorna:
    --------
    dict con métricas: R2, R2_ajustado, RMSE, MAE, MAPE
    """
    n = len(y_true)
    
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    
    # MAPE (cuidado con divisiones por cero)
    try:
        mape = mean_absolute_percentage_error(y_true, y_pred) * 100
    except:
        mape = np.nan
    
    # R² ajustado (requiere conocer p = número de features)
    # Lo calcularemos después cuando tengamos el modelo
    
    metricas = {
        'r2': r2,
        'rmse': rmse,
        'mae': mae,
        'mape': mape
    }
    
    return metricas

def target_encoding_regularizado(X_train, y_train, X_val, categorical_cols, m=10):
    """
    Target encoding con regularización para evitar overfitting.
    
    Como tu dataset tiene variables categóricas YA en formato OHE (0/1),
    esta función simplemente RETORNA LOS DATOS SIN MODIFICAR.
    
    Parámetros:
    -----------
    X_train : DataFrame
        Conjunto de entrenamiento
    y_train : Series
        Variable objetivo de entrenamiento
    X_val : DataFrame
        Conjunto de validación
    categorical_cols : list
        Lista de columnas categóricas a codificar
    m : int
        Parámetro de suavizado (mayor = más conservador)
    
    Retorna:
    --------
    X_train_encoded, X_val_encoded : DataFrames (sin cambios en este caso)
    encoding_maps : dict vacío
    """
    
    # VERIFICAR: ¿Las columnas categóricas son binarias (0/1)?
    # Si sí, NO aplicar target encoding (no tiene sentido)
    
    todas_binarias = True
    for col in categorical_cols:
        valores_unicos = X_train[col].nunique()
        if valores_unicos > 2:
            todas_binarias = False
            break
    
    if todas_binarias:
        # Variables YA están en formato OHE (0/1), no hacer nada
        print("  [INFO] Variables categóricas ya están en formato One-Hot (0/1)")
        print("  [INFO] Target encoding NO aplicable, retornando datos sin cambios")
        return X_train.copy(), X_val.copy(), {}
    
    # Si llegamos aquí, hay variables categóricas verdaderas
    # Aplicar target encoding regularizado
    
    X_train_encoded = X_train.copy()
    X_val_encoded = X_val.copy()
    
    # Media global del target
    mean_global = y_train.mean()
    
    encoding_maps = {}
    
    for col in categorical_cols:
        # Crear DataFrame temporal para cálculos
        temp_df = pd.DataFrame({
            'categoria': X_train_encoded[col],
            'target': y_train
        })
        
        # Calcular estadísticas por categoría
        stats = temp_df.groupby('categoria')['target'].agg(['mean', 'count']).reset_index()
        stats.columns = ['categoria', 'mean_cat', 'n_cat']
        
        # Aplicar fórmula de suavizado
        stats['encoded'] = (
            (stats['n_cat'] * stats['mean_cat'] + m * mean_global) / 
            (stats['n_cat'] + m)
        )
        
        # Crear diccionario de mapeo
        encoding_map = dict(zip(stats['categoria'], stats['encoded']))
        encoding_maps[col] = encoding_map
        
        # Aplicar encoding
        X_train_encoded[col + '_encoded'] = X_train_encoded[col].map(encoding_map).fillna(mean_global)
        X_val_encoded[col + '_encoded'] = X_val_encoded[col].map(encoding_map).fillna(mean_global)
        
        # Eliminar columna original
        X_train_encoded = X_train_encoded.drop(columns=[col])
        X_val_encoded = X_val_encoded.drop(columns=[col])
    
    return X_train_encoded, X_val_encoded, encoding_maps