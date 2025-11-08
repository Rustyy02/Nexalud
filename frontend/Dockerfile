FROM node:18-alpine

WORKDIR /app

# Copiar package.json primero
COPY package*.json ./

# Instalar dependencias
RUN npm install

# ✅ NO copiar el proyecto completo aquí (lo hace el volume)
# COPY . .

EXPOSE 3000

# ✅ Comando de desarrollo
CMD ["npm", "start"]