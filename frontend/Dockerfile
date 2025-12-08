FROM node:22

WORKDIR /app

# Copiar archivos de dependencias
COPY package.json package-lock.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY . .

# Exponer el puerto de Vite
EXPOSE 5173

# Comando para desarrollo (el flag --host es crucial para Docker)
CMD ["npm", "run", "dev", "--", "--host"]
